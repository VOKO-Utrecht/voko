from django import forms
from .models import OrderProduct, Order


class OrderProductForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['amount', 'product']
        widgets = {'product': forms.HiddenInput()}

    def clean_amount(self):
        amount = int(self.cleaned_data['amount'])
        if amount < 1:
            raise forms.ValidationError("Geen valide getal.")

        return amount


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = []