from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import os

class Ticket(models.Model):
    # Priority levels
    NORMAL = 'normal'
    PRIORITY = 'priority'
    URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (NORMAL, 'Normal (48 horas)'),
        (PRIORITY, 'Prioritario (24 horas)'),
        (URGENT, 'Urgente (8 horas)'),
    ]

    # Status options
    OPEN = 'open'
    IN_PROCESS = 'in_process'
    CLOSED = 'closed'

    STATUS_CHOICES = [
        (OPEN, 'Abierto'),
        (IN_PROCESS, 'En Proceso'),
        (CLOSED, 'Cerrado'),
    ]

    def attachment_path(instance, filename):
        # File will be uploaded to MEDIA_ROOT/tickets/<ticket_id>/<filename>
        return f'tickets/{instance.ticket_id}/{filename}'

    # Ticket fields
    ticket_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to=attachment_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # Time tracking
    resolution_time = models.DurationField(null=True, blank=True)

    # Priority and status
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default=NORMAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN)

    # Relationships
    requester_name = models.CharField(max_length=100)
    requester_email = models.EmailField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')

    def save(self, *args, **kwargs):
        # If status is changed to CLOSED, set closed_at time and calculate resolution_time
        if self.status == self.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
            self.resolution_time = self.closed_at - self.created_at

        # If status is changed from CLOSED to something else, reset closed_at and resolution_time
        if self.status != self.CLOSED and self.closed_at:
            self.closed_at = None
            self.resolution_time = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ticket #{self.ticket_id} - {self.subject}"

    def get_priority_color(self):
        """Returns Bootstrap color class based on priority"""
        if self.priority == self.URGENT:
            return 'danger'  # Red
        elif self.priority == self.PRIORITY:
            return 'warning'  # Yellow/Orange
        else:
            return 'info'  # Blue

    def get_status_color(self):
        """Returns Bootstrap color class based on status"""
        if self.status == self.OPEN:
            return 'secondary'  # Gray
        elif self.status == self.IN_PROCESS:
            return 'primary'  # Blue
        else:
            return 'success'  # Green

    def get_response_time_requirement(self):
        """Returns the required response time in hours based on priority"""
        if self.priority == self.URGENT:
            return 8
        elif self.priority == self.PRIORITY:
            return 24
        else:
            return 48

class TicketComment(models.Model):
    """Model for comments/updates on tickets"""
    comment_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='comments', to_field='ticket_id', db_column='ticket_id')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=100)  # For non-user commenters
    content = models.TextField()
    is_progress_update = models.BooleanField(default=False, help_text="Si este comentario es una actualización de progreso")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        comment_type = "Actualización del progreso" if self.is_progress_update else "Comentario"
        return f"{comment_type} ticket N° {self.ticket} por {self.author or self.author_name}"
