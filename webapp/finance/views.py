from braces.views import LoginRequiredMixin
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, FormView
from qantani import QantaniAPI
from finance.models import Payment


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

        user_debit = self.request.user.balance.debit()
        assert user_debit > 0
        bank_id = f.cleaned_data['bank']
        results = self._create_transaction(bank_id=bank_id,
                                           amount=user_debit,
                                           description="VOKO Utrecht ID %d" %
                                                       self.request.user.orders.get_current_order().id)

        Payment.objects.create(amount=user_debit,
                               order=self.request.user.orders.get_current_order(),
                               transaction_id=results.get("TransactionID"),
                               transaction_code=results.get("Code"))

        redirect_url = results.get("BankURL")
        return redirect(redirect_url)


class ConfirmTransactionView(LoginRequiredMixin, QantaniMixin, TemplateView):
    """
    Callback view, $bank redirects user back to this view after payment

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
            payment.succeeded = True
            payment.save()
            payment.order.finalized = True
            payment.order.save()
            payment.create_credit()

            payment.order.mail_confirmation()
            payment.order._notify_admins_about_new_order()

        context['payment_succeeded'] = success

        return context
