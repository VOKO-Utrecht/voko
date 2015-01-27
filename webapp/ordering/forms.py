from django import forms
from .models import OrderProduct, Order


class OrderProductForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['amount', 'product']
        widgets = {'product': forms.HiddenInput()}

    def clean(self):
        cleaned_data = super(OrderProductForm, self).clean()
        amount = cleaned_data.get('amount')

        if amount < 1:
            raise forms.ValidationError("Geen valide getal.")

        # When called from product detail view, check for max amount
        if 'product' in self.cleaned_data:
            product = cleaned_data.get('product')
            if product.amount_available is not None and amount > product.amount_available:
                raise forms.ValidationError("Dit aantal is niet beschikbaar.")

        return cleaned_data


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = []