from braces.views import LoginRequiredMixin
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView
from qantani import QantaniAPI


def choosebankform_factory(banks):
    choices = [(bank['Id'], bank['Name']) for bank in banks]

    class ChooseBankForm(forms.Form):
        bank = forms.ChoiceField(choices=choices)

    return ChooseBankForm


class QantaniMixin(object):
    def __init__(self, *args, **kwargs):
        self.qantani_api = QantaniAPI(settings.QANTANI_MERCHANT_ID,
                                      settings.QANTANI_MERCHANT_KEY,
                                      settings.QANTANI_MERCHANT_SECRET)

    def _create_transaction(self, bank_id, amount, description):
        self.qantani_api.create_ideal_transaction(amount=amount,
                                                  bank_id=bank_id,
                                                  description=description,
                                                  return_url=reverse('finance.confirmtransaction'))


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

        bank_id = f.cleaned_data['bank']
        self._create_transaction(bank_id=bank_id,
                                 amount=self.request.user.balance.debit(),
                                 description="VOKO Utrecht ID %d" % self.request.user.orders.get_current_order().id)


class ConfirmTransactionView(LoginRequiredMixin, TemplateView):
    """
    Callback view, $bank redirects user back to this view after payment

    Transaction details are sent in GET parameters.

    Validate payment.
    """
    def get(self, request, *args, **kwargs):
        pass
