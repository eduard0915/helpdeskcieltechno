from django import forms
from .models import Company

class CompanyForm(forms.ModelForm):
    """Form for creating and updating company information"""
    
    class Meta:
        model = Company
        fields = ['name', 'logo', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Mi Empresa S.A.'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ej. contacto@empresa.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. +34 900 000 000'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ej. Calle Falsa 123, Ciudad'}),
        }