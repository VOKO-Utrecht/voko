import Mollie
from braces.views import LoginRequiredMixin
from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, FormView, View
from qantani import QantaniAPI  # TODO remove
from finance.models import Payment
from log import log_event
from ordering.core import get_current_order_round
from ordering.models import Order


def choosebankform_factory(banks):
    """
    Generate a Django Form used to choose your bank from a drop down
    Based on the up-to-date list of :banks: from our PSP
    """
    choices = [(bank['id'], bank['name'])
               for bank in banks['data']
               if bank['method'] == Mollie.API.Object.Method.IDEAL]

    class ChooseBankForm(forms.Form):
        bank = forms.ChoiceField(choices=choices, required=True)

    return ChooseBankForm


class QantaniMixin(object):
    """
    Sugar coating for Qantani API calls used in our views
    """
    def __init__(self):
        self.qantani_api = QantaniAPI(settings.QANTANI_MERCHANT_ID,
                                      settings.QANTANI_MERCHANT_KEY,
                                      settings.QANTANI_MERCHANT_SECRET)

    def _create_transaction(self, bank_id, amount, description):
        return self.qantani_api.create_ideal_transaction(amount=amount,
                                                         bank_id=bank_id,
                                                         description=description,
                                                         return_url=(settings.BASE_URL +
                                                                     reverse('finance.confirmtransaction')))

    def _validate_transaction(self, transaction_code, transaction_checksum, transaction_id,
                              transaction_status, transaction_salt):

        if transaction_status != "1":
            return False

        return self.qantani_api.validate_transaction_checksum(transaction_checksum,
                                                              transaction_id,
                                                              transaction_code,
                                                              transaction_status,
                                                              transaction_salt)


class MollieMixin(object):
    def __init__(self):
        self.mollie = Mollie.API.Client()
        self.mollie.setApiKey(settings.MOLLIE_API_KEY)


class ChooseBankView(LoginRequiredMixin, MollieMixin, FormView):
    """
    Let user choose a bank to use for iDeal payment
    POSTs to CreateTransactionView.
    """
    template_name = "finance/choose_bank.html"

    def get_form_class(self):
        issuers = self.mollie.issuers.all()
        return choosebankform_factory(issuers)

    def get_context_data(self, **kwargs):
        context = super(ChooseBankView, self).get_context_data(**kwargs)
        cur_order_round = get_current_order_round()
        try:
            context['order'] = Order.objects.get(
                id=self.request.GET.get(
                    'order_to_pay',
                    Order.objects.get(paid=False, finalized=True,
                                      order_round=cur_order_round,
                                      user=self.request.user).id))
        except Order.DoesNotExist:
            pass  # Warning is shown in template

        return context


class CreateTransactionView(LoginRequiredMixin, QantaniMixin, FormView):
    """
    Create transaction @ bank and redirect user to bank URL
    """
    template_name = None

    def get_form_class(self):
        banks = self.qantani_api.get_ideal_banks()
        return choosebankform_factory(banks)

    def post(self, request, *args, **kwargs):
        Form = self.get_form_class()
        form = Form(data=request.POST)
        form.full_clean()

        if form.is_valid() is False:
            # Should not happen, as the form has just one input field. Redirect back to previous view
            return redirect(reverse('finance.choosebank'))

        order_to_pay = Order.objects.get(id=request.session['order_to_pay'])
        amount_to_pay = order_to_pay.total_price_to_pay_with_balances_taken_into_account()
        log_event(event="Initiating payment (creating transaction) for order %d and amount %f" %
                  (order_to_pay.id, amount_to_pay), user=order_to_pay.user)

        # Sanity checks. If one of these fails, it's very likely that someone is tampering.
        assert order_to_pay.user == request.user
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False
        assert order_to_pay.payments.filter(succeeded=True).exists() is False

        if order_to_pay.order_round.is_open is not True:
            messages.error(request, "De bestelronde is gesloten, je kunt niet meer betalen.")
            log_event(event="Payment for order %s canceled because order round %s is closed" %
                            (order_to_pay.id, order_to_pay.order_round.id), user=order_to_pay.user)
            return redirect(reverse('finish_order', args=(order_to_pay.id,)))

        bank_id = form.cleaned_data['bank']
        results = self._create_transaction(bank_id=bank_id,
                                           amount=amount_to_pay,
                                           description="VOKO Utrecht ID %d" % order_to_pay.id)

        Payment.objects.create(amount=amount_to_pay,
                               order=order_to_pay,
                               transaction_id=results["TransactionID"],
                               transaction_code=results["Code"])

        redirect_url = results["BankURL"]
        return redirect(redirect_url)


class ConfirmTransactionView(LoginRequiredMixin, QantaniMixin, TemplateView):
    """
    $bank redirects user back to this view after payment, or after payment was canceled.
    Transaction details are sent in GET parameters.

    Validate the payment and finish order when valid.
    """
    template_name = "finance/after_payment.html"

    def get_context_data(self, **kwargs):
        context = super(ConfirmTransactionView, self).get_context_data(**kwargs)
        transaction_id = self.request.GET['id']
        transaction_status = self.request.GET['status']
        transaction_salt = self.request.GET['salt']
        transaction_checksum = self.request.GET['checksum']

        payment = get_object_or_404(Payment, transaction_id=transaction_id, succeeded=False)
        transaction_code = payment.transaction_code

        success = self._validate_transaction(transaction_code, transaction_checksum,
                                             transaction_id, transaction_status, transaction_salt)

        if success:
            assert payment.order.finalized is True
            assert payment.order.paid is False
            assert payment.order.order_round.is_open is True

            payment.succeeded = True
            payment.save()

            payment.create_and_link_credit()
            payment.order.complete_after_payment()

            log_event(event="Payment %s for order %s and amount %f succeeded" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)

            del self.request.session['order_to_pay']

        else:
            log_event(event="Payment %s for order %s and amount %f failed" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)

        context['payment_succeeded'] = success
        return context


class QantaniCallbackView(QantaniMixin, View):
    """
    Web hook, for when users close their browser after payment...
    See http://www.easy-ideal.com/callback-url/
    """
    def get(self, request, *args, **kwargs):
        transaction_id = request.GET.get('id')
        transaction_status = request.GET.get('status')
        transaction_salt = request.GET.get('salt')
        transaction_checksum = request.GET.get('checksum1')

        payment = get_object_or_404(Payment, transaction_id=transaction_id)
        transaction_code = payment.transaction_code

        success = self._validate_transaction(transaction_code, transaction_checksum,
                                             transaction_id, transaction_status, transaction_salt)

        if not success:
            log_event(event="Payment %s for order %s and amount %f failed via callback" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)
            return HttpResponse("")  # Any other response than "+" means failure.

        # Successful payment!

        payment.succeeded = True
        payment.save()
        payment.create_and_link_credit()
        log_event(event="Payment %s for order %s and amount %f succeeded via callback" %
                        (payment.id, payment.order.id, payment.amount), user=payment.order.user)

        if payment.order.paid is False:
            # Order has not been paid, but the payment has now been confirmed and credit has been created.
            # Time to finish the order, if the order round is still open.

            # Sanity Check
            assert payment.order.finalized is True

            if payment.order.order_round.is_open:
                payment.order.complete_after_payment()
            else:
                # Corner case where payment was executed before closing time, but never finished (user
                # closed browser tab), the payment is now validated by callback, but order round is closed and our
                # suppliers likely have been mailed the totals. Credit for the user has just been created, but we don't
                # want to complete the order because it was placed too late.
                log_event(event="Order round %s is closed, so not finishing order %s via callback!" % (
                    payment.order.order_round.id, payment.order.id
                ), user=payment.order.user)

                payment.order.mail_failure_notification()

        return HttpResponse("+")  # This is the official "success" response


class CancelPaymentView(View):
    """
    When user clicks 'cancel' on the ChooseBankView.
    """
    def get(self, request, *args, **kwargs):
        order_to_pay = Order.objects.get(id=request.session['order_to_pay'])

        # Sanity checks
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False

        order_to_pay.finalized = False
        order_to_pay.save()

        log_event(event="Payment for order %s canceled" % order_to_pay.id, user=order_to_pay.user)

        return HttpResponseRedirect(reverse("finish_order", args=(order_to_pay.pk,)))
