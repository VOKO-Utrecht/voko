from django import forms
from .models import OrderProduct


class OrderForm(forms.ModelForm):
    class Meta:
        model = OrderProduct
        fields = ['amount']
