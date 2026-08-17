from django import forms
from .models import BloodStock, BloodRequest
from django.utils import timezone

class StockForm(forms.ModelForm):
    class Meta:
        model = BloodStock
        fields = ['blood_group', 'quantity', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_expiry_date(self):
        date = self.cleaned_data['expiry_date']
        if date < timezone.now().date():
            raise forms.ValidationError("Expiry date cannot be in the past.")
        return date


class RequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['requester_name', 'hospital_name', 'blood_group', 'quantity_needed', 'required_by_date']
        widgets = {
            'required_by_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_quantity_needed(self):
        qty = self.cleaned_data['quantity_needed']
        if qty <= 0:
            raise forms.ValidationError("Quantity must be at least 1 unit.")
        return qty