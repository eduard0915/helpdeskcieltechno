import os

from django import forms
from django.contrib.auth.models import User

from .models import Ticket, TicketComment

# Extensiones permitidas para adjuntos (evita XSS almacenado con HTML/SVG ejecutable)
ALLOWED_ATTACHMENT_EXTENSIONS = {
    'pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'csv', 'zip', 'rar', '7z', 'jpg', 'jpeg', 'png', 'gif',
    'bmp', 'webp', 'odt', 'ods', 'odp',
}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB

class TicketForm(forms.ModelForm):
    """Form for creating a new ticket"""
    class Meta:
        model = Ticket
        fields = [
            'subject', 'description', 'attachment', 'priority',
            'requester_name', 'requester_email',
        ]
        widgets = {
            'subject': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej. No puedo acceder a mi cuenta'}
            ),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Ej. Al intentar iniciar sesión, el sistema muestra un error de conexión...',
                }
            ),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'requester_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej. Juan Pérez'}
            ),
            'requester_email': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej. juan@ejemplo.com'}
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            self.fields['requester_name'].required = False
            self.fields['requester_email'].required = False

    def clean_attachment(self):
        """Valida extensión y tamaño del adjunto para evitar XSS almacenado."""
        attachment = self.cleaned_data.get('attachment')
        if not attachment:
            return attachment

        ext = os.path.splitext(attachment.name)[1].lower().lstrip('.')
        if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
            raise forms.ValidationError(
                'Tipo de archivo no permitido. Extensiones válidas: '
                + ', '.join(sorted(ALLOWED_ATTACHMENT_EXTENSIONS))
            )
        if attachment.size > MAX_ATTACHMENT_SIZE:
            raise forms.ValidationError('El archivo no puede superar los 10 MB.')

        return attachment

class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        full_name = obj.get_full_name()
        if full_name:
            return f"{full_name} ({obj.username})"
        return obj.username

class TicketUpdateForm(forms.ModelForm):
    """Form for updating an existing ticket (admin/staff only)"""
    assigned_to = UserModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Ticket
        fields = ['status', 'priority', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff users as assignees
        self.fields['assigned_to'].queryset = (
            User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
        )

class TicketCommentForm(forms.ModelForm):
    """Form for adding comments to a ticket"""
    class Meta:
        model = TicketComment
        fields = ['content', 'is_progress_update']
        widgets = {
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Añadir un comentario...'}
            ),
            'is_progress_update': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        # Get the user from kwargs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Only show progress update option to staff users
        if user and not user.is_staff:
            self.fields.pop('is_progress_update')
        else:
            self.fields['is_progress_update'].label = "Marcar como actualización de progreso (notificará al cliente)"

class TicketSearchForm(forms.Form):
    """Form for searching tickets"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar tickets...'})
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