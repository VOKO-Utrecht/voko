from django import forms
from .models import OrderProduct, Order


class OrderProductForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['amount']


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order