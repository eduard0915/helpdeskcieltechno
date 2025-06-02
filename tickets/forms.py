from django import forms
from django.contrib.auth.models import User
from .models import Ticket, TicketComment

class TicketForm(forms.ModelForm):
    """Form for creating a new ticket"""
    class Meta:
        model = Ticket
        fields = ['subject', 'description', 'priority', 'requester_name', 'requester_email']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'requester_name': forms.TextInput(attrs={'class': 'form-control'}),
            'requester_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class TicketUpdateForm(forms.ModelForm):
    """Form for updating an existing ticket (admin/staff only)"""
    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff users as assignees
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        self.fields['assigned_to'].required = False

class TicketCommentForm(forms.ModelForm):
    """Form for adding comments to a ticket"""
    class Meta:
        model = TicketComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment...'}),
        }

class TicketSearchForm(forms.Form):
    """Form for searching tickets"""
    search = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search tickets...'})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + list(Ticket.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[('', 'All')] + list(Ticket.PRIORITY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )