# finances/forms.py

from django import forms
from .models import Income, Expense
from django.forms import ModelForm

class IncomeForm(ModelForm):
    class Meta:
        model = Income
        fields = ['amount', 'description', 'date']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),  # This makes the date field a date picker
        }

class ExpenseForm(ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'description', 'date']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),  # This makes the date field a date picker
        }
