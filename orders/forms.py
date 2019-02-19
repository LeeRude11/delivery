from django import forms


class AmountForm(forms.Form):
    amount = forms.IntegerField(label='Amount')
