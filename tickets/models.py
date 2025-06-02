from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Ticket(models.Model):
    # Priority levels
    NORMAL = 'normal'
    PRIORITY = 'priority'
    URGENT = 'urgent'

    PRIORITY_CHOICES = [
        (NORMAL, 'Normal (48 hours)'),
        (PRIORITY, 'Priority (24 hours)'),
        (URGENT, 'Urgent (8 hours)'),
    ]

    # Status options
    OPEN = 'open'
    IN_PROCESS = 'in_process'
    CLOSED = 'closed'

    STATUS_CHOICES = [
        (OPEN, 'Open'),
        (IN_PROCESS, 'In Process'),
        (CLOSED, 'Closed'),
    ]

    # Ticket fields
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
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
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=100)  # For non-user commenters
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.ticket} by {self.author or self.author_name}"
