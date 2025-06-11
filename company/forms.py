from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):
    """Form for creating and updating company information"""
    
    class Meta:
        model = Company
        fields = ['name', 'logo', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }