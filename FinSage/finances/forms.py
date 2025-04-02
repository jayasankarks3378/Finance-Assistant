# finances/forms.py

from django import forms
from .models import Income, Expense,BillUpload
from django.forms import ModelForm

class IncomeForm(ModelForm):
    class Meta:
        model = Income
        fields = ['amount', 'description', 'date', 'category']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),  # This makes the date field a date picker
        }

class ExpenseForm(ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'description', 'date','category']

        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),  # This makes the date field a date picker
        }

class BillUploadForm(forms.ModelForm):
    class Meta:
        model = BillUpload
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'accept': 'image/*'}) 
        }

class FinancialAnalysisForm(forms.Form):
    PERIOD_CHOICES = [
        ('all', 'All Time'),
        ('month', 'Current Month'),
        ('year', 'Current Year'),
    ]
    
    ANALYSIS_CHOICES = [
        ('overview', 'Financial Overview'),
        ('spending', 'Spending Analysis'),
        ('saving', 'Saving Opportunities'),
        ('trends', 'Financial Trends'),
    ]
    
    period = forms.ChoiceField(choices=PERIOD_CHOICES, required=False)
    analysis_type = forms.ChoiceField(choices=ANALYSIS_CHOICES, required=False)