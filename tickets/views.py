import uuid

from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

from .models import Ticket, TicketComment
from .forms import TicketForm, TicketUpdateForm, TicketCommentForm, TicketSearchForm

def home(request):
    """Home page with dashboard showing ticket counts by status"""
    # Get counts for each status
    status_counts = Ticket.objects.values('status').annotate(count=Count('status'))

    # Convert to a more usable format
    counts = {
        'open': 0,
        'in_process': 0,
        'closed': 0,
        'total': Ticket.objects.count()
    }

    for item in status_counts:
        counts[item['status']] = item['count']

    # Get recent tickets
    recent_tickets = Ticket.objects.order_by('-created_at')[:5]

    context = {
        'counts': counts,
        'recent_tickets': recent_tickets,
    }

    return render(request, 'tickets/home.html', context)

def create_ticket(request):
    """View for creating a new ticket"""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save()
            # Send confirmation email
            send_ticket_confirmation_email(ticket)
            messages.success(request, f'Su ticket se ha enviado correctamente. Su ID de ticket es {ticket.ticket_id}')
            return redirect('ticket_detail', ticket_id=ticket.ticket_id)
    else:
        form = TicketForm()
    context = {
        'form': form,
        'title': 'Enviar un Ticket',
    }
    return render(request, 'tickets/create_ticket.html', context)

def ticket_detail(request, ticket_id):
    """View for displaying ticket details"""
    ticket = Ticket.objects.get(ticket_id=ticket_id)

    # Prefetch comments con autor para evitar N+1 queries
    comments = ticket.comments.select_related('author').order_by('created_at')
    # comments = TicketComment.objects.filter(ticket=ticket.ticket_id).select_related('author').order_by('created_at')

    # Procesamiento del formulario de comentarios
    if request.method == 'POST' and 'comment_submit' in request.POST:
        comment_form = TicketCommentForm(request.POST, user=request.user)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.ticket = ticket

            if request.user.is_authenticated:
                comment.author = request.user
                comment.author_name = request.user.get_full_name() or request.user.username
            else:
                comment.author_name = 'Anonymous'

            comment.save()

            if comment.is_progress_update and request.user.is_staff:
                try:
                    send_progress_update_email(ticket, comment)
                    messages.success(request,
                                     'Se agregó actualización de progreso y se envió una notificación al cliente.')
                except Exception as e:
                    messages.warning(request,
                                     f'Se agregó una actualización de progreso, pero no se pudo enviar la notificación: {str(e)}')
            else:
                messages.success(request, 'Su comentario ha sido añadido.')

            return redirect('ticket_detail', ticket_id=ticket.ticket_id)
    else:
        comment_form = TicketCommentForm(user=request.user)

    context = {
        'ticket': ticket,
        'comments': comments,
        'comment_form': comment_form,
    }

    if request.user.is_authenticated and request.user.is_staff:
        if request.method == 'POST' and 'update_submit' in request.POST:
            update_form = TicketUpdateForm(request.POST, instance=ticket)
            if update_form.is_valid():
                old_status = ticket.status
                updated_ticket = update_form.save()

                if old_status != Ticket.CLOSED and updated_ticket.status == Ticket.CLOSED:
                    send_ticket_closed_email(updated_ticket)

                messages.success(request, 'El ticket se ha actualizado correctamente.')
                return redirect('ticket_detail', ticket_id=ticket.ticket_id)
        else:
            update_form = TicketUpdateForm(instance=ticket)

        context['update_form'] = update_form

    return render(request, 'tickets/ticket_detail.html', context)

@login_required
def manage_tickets(request):
    """View for staff to manage all tickets"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')

    # Initialize search form
    form = TicketSearchForm(request.GET)
    tickets = Ticket.objects.all().order_by('-created_at')

    # Apply filters if form is valid
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        priority = form.cleaned_data.get('priority')

        if search:
            tickets = tickets.filter(subject__icontains=search) | tickets.filter(description__icontains=search) | tickets.filter(requester_email__icontains=search)

        if status:
            tickets = tickets.filter(status=status)

        if priority:
            tickets = tickets.filter(priority=priority)

    context = {
        'tickets': tickets,
        'form': form,
    }

    return render(request, 'tickets/manage_tickets.html', context)

@login_required
def my_assigned_tickets(request):
    """View for staff to see tickets assigned to them"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')

    tickets = Ticket.objects.filter(assigned_to=request.user).order_by('-created_at')

    context = {
        'tickets': tickets,
    }

    return render(request, 'tickets/my_assigned_tickets.html', context)

def check_ticket_status(request):
    """View for users to check the status of their ticket"""
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        email = request.POST.get('email')

        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id, requester_email=email)
            return redirect('ticket_detail', ticket_id=ticket.ticket_id)
        except Ticket.DoesNotExist:
            messages.error(request, 'No se encontró ningún ticket con esa combinación de ID y correo electrónico.')

    return render(request, 'tickets/check_ticket.html')

@login_required
def my_tickets(request):
    """View for clients to see their ticket history"""
    # Get tickets for the current user's email
    tickets = Ticket.objects.filter(requester_email=request.user.email).order_by('-created_at')

    context = {
        'tickets': tickets,
        'title': 'Mis Tickets',
    }

    return render(request, 'tickets/my_tickets.html', context)

# Email functions
def send_progress_update_email(ticket, comment):
    """Send notification email when a progress update is added to a ticket"""
    subject = f'Actualización en su Ticket #{ticket.ticket_id}'

    # Build the ticket URL
    ticket_url = reverse('ticket_detail', kwargs={'ticket_id': ticket.ticket_id})
    absolute_url = f"{settings.SITE_URL}{ticket_url}" if hasattr(settings, 'SITE_URL') else ticket_url

    # Create HTML message
    html_message = render_to_string('tickets/emails/ticket_update.html', {
        'ticket': ticket,
        'comment': comment,
        'ticket_url': absolute_url,
    })

    # Create plain text message
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [ticket.requester_email],
        html_message=html_message,
        fail_silently=False,
    )

def send_ticket_confirmation_email(ticket):
    """Send confirmation email when a ticket is created"""
    subject = f'Helpdesk Ticket #{ticket.ticket_id} Received'

    # Build the ticket URL
    ticket_url = reverse('ticket_detail', kwargs={'ticket_id': ticket.ticket_id})
    absolute_url = f"{settings.SITE_URL}{ticket_url}" if hasattr(settings, 'SITE_URL') else ticket_url

    # Create HTML message
    html_message = render_to_string('tickets/emails/ticket_confirmation.html', {
        'ticket': ticket,
        'ticket_url': absolute_url,
    })

    # Create plain text message
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [ticket.requester_email],
        html_message=html_message,
        fail_silently=False,
    )

def send_ticket_closed_email(ticket):
    """Send notification email when a ticket is closed"""
    subject = f'Su Ticket de soporte técnico # {ticket.ticket_id} ha sido Cerrado'

    # Build the ticket URL
    ticket_url = reverse('ticket_detail', kwargs={'ticket_id': ticket.ticket_id})
    absolute_url = f"{settings.SITE_URL}{ticket_url}" if hasattr(settings, 'SITE_URL') else ticket_url

    # Create HTML message
    html_message = render_to_string('tickets/emails/ticket_closed.html', {
        'ticket': ticket,
        'ticket_url': absolute_url,
        'resolution_time': ticket.resolution_time,
    })

    # Create plain text message
    plain_message = strip_tags(html_message)

    # Send email
    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [ticket.requester_email],
        html_message=html_message,
        fail_silently=False,
    )
