from mollie.api.client import Client as MollieClient
from mollie.api.resources.methods import Method as MollieMethods
from braces.views import LoginRequiredMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, FormView, View
from finance.models import Payment
from log import log_event
from ordering.core import get_current_order_round
from ordering.models import Order


def choosebankform_factory(banks, methods):
    """
    Generate a Django Form used to choose your bank from a drop down
    Based on the up-to-date list of :banks: from our PSP
    """
    paymethods = [(method['id'], method['description'])
                  for method in methods
                  if method['status'] == 'activated']

    bankchoices = [(bank['id'], bank['name'])
                   for bank in banks]

    class ChooseBankForm(forms.Form):
        method = forms.ChoiceField(
            choices=paymethods,
            required=True,
            initial='ideal',
            widget=forms.RadioSelect,
            label="Betaalwijze")
        bank = forms.ChoiceField(choices=bankchoices, required=True)

    return ChooseBankForm


def get_order_to_pay(user):
    cur_order_round = get_current_order_round()

    return Order.objects.filter(paid=False, finalized=True,
                                order_round=cur_order_round,
                                user=user).last()


class MollieMixin(object):
    def __init__(self):
        self.mollie = MollieClient()
        self.mollie.set_api_key(settings.MOLLIE_API_KEY)
        self.issuers = self.get_ideal_issuers()
        self.methods = self.mollie.methods.all(include='issuers')

    def create_payment(self, amount, description, issuer_id, order_id, method):
        if (method == 'ideal'):
            mollieMethod = MollieMethods.IDEAL
        else:
            # Bancontact used to be called MisterCash
            mollieMethod = MollieMethods.MISTERCASH

        # Mollie API wants exactly two decimals, always
        return self.mollie.payments.create({
            'amount': {'currency':'EUR', 'value':"{0:.2f}".format(amount)},
            'description': description,
            'redirectUrl': (
                    settings.BASE_URL +
                    reverse("finance.confirmtransaction") +
                    "?order=%s" % order_id
            ),
            'webhookUrl': settings.BASE_URL + reverse("finance.callback"),
            'method': mollieMethod,
            'issuer': issuer_id,
            'metadata': {
                'order_id': order_id
            },
        })

    def get_ideal_issuers(self):
        ideal_method = self.mollie.methods.get('ideal', include='issuers')
        return ideal_method['issuers']

    def get_payment(self, payment_id):
        return self.mollie.payments.get(payment_id)


class ChooseBankView(LoginRequiredMixin, MollieMixin, FormView):
    """
    Let user choose a bank to use for iDeal payment
    """
    template_name = "finance/choose_bank.html"

    def get_form_class(self):
        return choosebankform_factory(banks=self.issuers,
                                      methods=self.methods)

    def get_context_data(self, **kwargs):
        context = super(ChooseBankView, self).get_context_data(**kwargs)
        context['order'] = get_order_to_pay(self.request.user)
        return context


class CreateTransactionView(LoginRequiredMixin, MollieMixin, FormView):
    """
    Create transaction @ bank and redirect user to bank URL
    """

    def get_form_class(self):
        return choosebankform_factory(banks=self.issuers, methods=self.methods)

    def post(self, request, *args, **kwargs):
        Form = self.get_form_class()
        form = Form(data=request.POST)
        form.full_clean()

        # input validation
        if 'method' not in form.cleaned_data:
            return redirect(reverse('finance.choosebank'))
        method = form.cleaned_data.get('method')

        if (method == 'ideal'):
            if 'bank' not in form.cleaned_data:
                return redirect(reverse('finance.choosebank'))
            bank = form.cleaned_data.get('bank')
        else:
            bank = None
        # end input validation

        order_to_pay = get_order_to_pay(request.user)
        if not order_to_pay:
            messages.error(request, "Geen bestelling gevonden")
            return redirect(reverse('view_products'))

        amount_to_pay = order_to_pay\
            .total_price_to_pay_with_balances_taken_into_account()
        log_event(
            event="Initiating payment (creating transaction) for order %d "
                  "and amount %f" %
                  (order_to_pay.id, amount_to_pay), user=order_to_pay.user)

        # Sanity checks. If one of these fails, it's very likely that someone
        # is tampering.
        assert order_to_pay.user == request.user
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False
        assert order_to_pay.payments.filter(succeeded=True).exists() is False

        if order_to_pay.order_round.is_open is not True:
            messages.error(request,
                           "De bestelronde is gesloten, "
                           "je kunt niet meer betalen.")
            log_event(
                event="Payment for order %s canceled because "
                      "order round %s is closed" %
                      (order_to_pay.id, order_to_pay.order_round.id),
                user=order_to_pay.user)
            return redirect(reverse('finish_order', args=(order_to_pay.id,)))

        # Start the payment
        results = self.create_payment(
                                    amount=float(amount_to_pay),
                                    description="VOKO Utrecht %d"
                                                % order_to_pay.id,
                                    issuer_id=bank,
                                    order_id=order_to_pay.id,
                                    method=method)

        Payment.objects.create(amount=amount_to_pay,
                               order=order_to_pay,
                               mollie_id=results["id"])

        redirect_url = results.checkout_url
        return redirect(redirect_url)


class ConfirmTransactionView(LoginRequiredMixin, MollieMixin, TemplateView):
    """
    $bank redirects user back to this view after payment, or after payment
    was canceled.
    Transaction details are sent in GET parameters.

    Validate the payment and finish order when valid.
    """
    template_name = "finance/after_payment.html"

    def get_context_data(self, **kwargs):
        context = super(ConfirmTransactionView, self).get_context_data(
            **kwargs)

        order_id = self.request.GET.get('order')

        # Payment may already be confirmed by the webhook
        try:
            order = Order.objects.get(id=order_id, user=self.request.user)
        except Order.DoesNotExist:
            raise Http404

        if order.paid is True:
            context['payment_succeeded'] = True
            return context

        payment = Payment.objects.filter(order__id=order_id,
                                         succeeded=False,)\
            .order_by('id').last()

        if payment is None:
            raise Http404

        mollie_payment = self.get_payment(payment.mollie_id)
        success = mollie_payment.isPaid()

        if success:
            if (payment.order.finalized is True and
                    payment.order.paid is False and
                    payment.order.order_round.is_open is True):

                payment.succeeded = True
                payment.save()

                payment.create_and_link_credit()
                payment.order.complete_after_payment()

                log_event(
                    event="Payment %s for order %s and amount %f succeeded" %
                          (payment.id, payment.order.id, payment.amount),
                    user=payment.order.user)

            else:
                log_event(event="Payment %s was already paid" % payment.id,
                          user=payment.order.user)

        else:
            log_event(event="Payment %s for order %s and amount %f failed" %
                            (payment.id, payment.order.id, payment.amount),
                      user=payment.order.user)

        context['payment_succeeded'] = success
        return context


class PaymentWebHook(MollieMixin, View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(PaymentWebHook, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        mollie_id = request.POST.get('id')

        payment = get_object_or_404(Payment, mollie_id=mollie_id)
        mollie_payment = self.get_payment(payment.mollie_id)
        success = mollie_payment.isPaid()

        if not success:
            log_event(
                event="Payment %s for order %s and amount %f "
                      "failed via callback" %
                      (payment.id, payment.order.id, payment.amount),
                user=payment.order.user)
            return HttpResponse("")

        # Successful payment!
        payment.succeeded = True
        payment.save()

        payment.create_and_link_credit()
        log_event(
            event="Payment %s for order %s and amount %f "
                  "succeeded via callback" %
                  (payment.id, payment.order.id, payment.amount),
            user=payment.order.user)

        if payment.order.paid is False:
            # Order has not been paid, but the payment has now been confirmed
            # and credit has been created.
            # Time to finish the order, if the order round is still open.

            # Sanity Check
            assert payment.order.finalized is True

            if payment.order.order_round.is_open:
                payment.order.complete_after_payment()
            else:
                # Corner case where payment was executed before closing time,
                # but never finished (user closed browser tab),
                # the payment is now validated by callback, but order round is
                # closed and our suppliers likely have been mailed the totals.
                # Credit for the user has just been created, but we don't
                # want to complete the order because it was placed too late.
                log_event(
                    event="Order round %s is closed, so not finishing "
                          "order %s via callback!" % (
                              payment.order.order_round.id,
                              payment.order.id),
                    user=payment.order.user)

                payment.order.mail_failure_notification()

        return HttpResponse("")


class CancelPaymentView(View):
    """
    When user clicks 'cancel' on the ChooseBankView.
    """

    def get(self, request, *args, **kwargs):
        order_to_pay = get_order_to_pay(request.user)
        if not order_to_pay:
            messages.error(request, "Geen bestelling gevonden")
            return redirect(reverse('view_products'))

        # Sanity checks
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False

        order_to_pay.finalized = False
        order_to_pay.save()

        log_event(event="Payment for order %s canceled" % order_to_pay.id,
                  user=order_to_pay.user)

        return HttpResponseRedirect(
            reverse("finish_order", args=(order_to_pay.pk,)))
