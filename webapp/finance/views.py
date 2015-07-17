from braces.views import LoginRequiredMixin
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, FormView, View
from qantani import QantaniAPI
from finance.models import Payment
from log import log_event
from ordering.models import Order


def choosebankform_factory(banks):
    choices = [(bank['Id'], bank['Name']) for bank in banks]

    class ChooseBankForm(forms.Form):
        bank = forms.ChoiceField(choices=choices)

    return ChooseBankForm


class QantaniMixin(object):
    def __init__(self):
        self.qantani_api = QantaniAPI(settings.QANTANI_MERCHANT_ID,
                                      settings.QANTANI_MERCHANT_KEY,
                                      settings.QANTANI_MERCHANT_SECRET)

    def _create_transaction(self, bank_id, amount, description):
        return self.qantani_api.create_ideal_transaction(amount=amount,
                                                         bank_id=bank_id,
                                                         description=description,
                                                         return_url=settings.BASE_URL + reverse('finance.confirmtransaction'))

    def _validate_transaction(self, transaction_code, transaction_checksum, transaction_id,
                              transaction_status, transaction_salt):

        if transaction_status != "1":
            return False

        return self.qantani_api.validate_transaction_checksum(transaction_checksum,
                                                              transaction_id,
                                                              transaction_code,
                                                              transaction_status,
                                                              transaction_salt)


class ChooseBankView(LoginRequiredMixin, QantaniMixin, FormView):
    """
    Lets user choose bank to pay.
    POSTs to CreateTransactionView.
    """
    template_name = "finance/choose_bank.html"

    def get_form_class(self):
        banks = self.qantani_api.get_ideal_banks()
        return choosebankform_factory(banks)

    def get_context_data(self, **kwargs):
        context = super(ChooseBankView, self).get_context_data(**kwargs)
        context['order'] = Order.objects.get(id=self.request.session['order_to_pay'])
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
        form = self.get_form_class()
        f = form(data=request.POST)
        if not f.is_valid():
            # Should not happen. Redirect back to prev. view
            redirect(reverse('finance.choosebank'))

        order_to_pay = Order.objects.get(id=request.session['order_to_pay'])
        amount_to_pay = order_to_pay.total_price_to_pay_with_balances_taken_into_account()
        log_event(event="Initiating payment (creating transaction) for order %d and amount %f" %
                  (order_to_pay.id, amount_to_pay), user=order_to_pay.user)

        assert order_to_pay.user == request.user
        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False
        assert order_to_pay.debit is None

        bank_id = f.cleaned_data['bank']
        results = self._create_transaction(bank_id=bank_id,
                                           amount=amount_to_pay,
                                           description="VOKO Utrecht ID %d" % order_to_pay.id)

        Payment.objects.create(amount=amount_to_pay,
                               order=order_to_pay,
                               transaction_id=results.get("TransactionID"),
                               transaction_code=results.get("Code"))

        redirect_url = results.get("BankURL")
        return redirect(redirect_url)


class ConfirmTransactionView(LoginRequiredMixin, QantaniMixin, TemplateView):
    """
    $bank redirects user back to this view after payment

    Transaction details are sent in GET parameters.

    Validate payment.
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

            payment.succeeded = True
            payment.save()
            payment.order.paid = True
            payment.order.save()
            payment.create_credit()
            log_event(event="Payment %s for order %s and amount %f succeeded" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)

            payment.order.complete_after_payment()

            del self.request.session['order_to_pay']

        else:
            log_event(event="Payment %s for order %s and amount %f failed" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)

        context['payment_succeeded'] = success

        return context


class QantaniCallbackView(QantaniMixin, View):
    """
    For extra certainty. See http://www.easy-ideal.com/callback-url/
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
            log_event(event="Payment %s for order %s and amount %f failed" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)
            return HttpResponse("")  # Any other response than "+" means failure.

        payment.succeeded = True
        payment.save()

        if payment.order.paid is False:
            # This means that the user paid, but closed the browser after confirming. The callback view enables
            # us to finish the order anyway.

            assert payment.order.finalized is True

            log_event(event="Payment %s for order %s and amount %f succeeded via callback" %
                      (payment.id, payment.order.id, payment.amount), user=payment.order.user)

            payment.order.paid = True
            payment.order.save()
            payment.create_credit()
            payment.order.complete_after_payment()

            del self.request.session['order_to_pay']

        return HttpResponse("+")  # This is the official "success" response


class CancelPaymentView(View):
    """
    When user clicks 'cancel' on the choosebankview
    """

    def get(self, request, *args, **kwargs):
        order_to_pay = Order.objects.get(id=request.session['order_to_pay'])

        assert order_to_pay.finalized is True
        assert order_to_pay.paid is False

        order_to_pay.finalized = False
        order_to_pay.save()

        log_event(event="Payment for order %s canceled" % order_to_pay.id, user=order_to_pay.user)

        return HttpResponseRedirect(reverse("finish_order", args=(order_to_pay.pk,)))
