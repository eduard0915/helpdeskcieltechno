import uuid

from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.db.models.functions import Coalesce, TruncMonth
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import views as auth_views
import json

from .models import Ticket, TicketComment
from .forms import TicketForm, TicketUpdateForm, TicketCommentForm, TicketSearchForm

def landing(request):
    """Página de inicio (landing page) con diseño de dos columnas"""
    return render(request, 'tickets/home.html')

class CustomLoginView(auth_views.LoginView):
    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse('manage_tickets')
        return reverse('my_tickets')

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

    # Get recent tickets (to be removed from UI per request, but kept here if needed elsewhere)
    recent_tickets = Ticket.objects.order_by('-created_at')[:5]

    # Average response time by ticket type (priority) for CLOSED tickets
    # Response time is from created_at to closed_at. Prefer stored resolution_time when available.
    avg_expr = Coalesce(
        'resolution_time',
        ExpressionWrapper(F('closed_at') - F('created_at'), output_field=DurationField())
    )
    avg_by_priority_qs = (
        Ticket.objects.filter(status=Ticket.CLOSED, closed_at__isnull=False)
        .values('priority')
        .annotate(avg_duration=Avg(avg_expr))
    )

    # Prepare a complete mapping for all priorities, even if none closed yet
    avg_by_priority = {
        Ticket.NORMAL: None,
        Ticket.PRIORITY: None,
        Ticket.URGENT: None,
    }
    for row in avg_by_priority_qs:
        avg_by_priority[row['priority']] = row['avg_duration']

    def format_timedelta(td):
        if not td:
            return '—'
        total_seconds = int(td.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        days = hours // 24
        hours = hours % 24
        if days > 0:
            return f"{days} d {hours} h {minutes} min"
        return f"{hours} h {minutes} min"

    avg_by_priority_display = {
        'normal': format_timedelta(avg_by_priority[Ticket.NORMAL]),
        'priority': format_timedelta(avg_by_priority[Ticket.PRIORITY]),
        'urgent': format_timedelta(avg_by_priority[Ticket.URGENT]),
    }

    # Build datasets for charts (last 12 full months including current month)
    now = timezone.now()
    # Calculate the first day of current month, then go back 11 months
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    months = []  # datetime objects representing month starts
    for i in range(11, -1, -1):
        # Compute month start i months ago
        year = first_of_this_month.year
        month = first_of_this_month.month - i
        while month <= 0:
            month += 12
            year -= 1
        months.append(first_of_this_month.replace(year=year, month=month))

    # Labels in Spanish short month names
    month_names = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    chart_labels = [f"{month_names[m.month-1]} {m.year}" for m in months]

    # Helper to align aggregated data by TruncMonth key
    def align_counts(qs, key='count'):
        mapping = {row['m'].date(): row[key] for row in qs}
        result = []
        for m in months:
            result.append(int(mapping.get(m.date(), 0)))
        return result

    # Created per month
    created_qs = (
        Ticket.objects
        .filter(created_at__gte=months[0])
        .annotate(m=TruncMonth('created_at'))
        .values('m')
        .annotate(count=Count('ticket_id'))
        .order_by('m')
    )
    created_counts = align_counts(created_qs)

    # Closed per month
    closed_qs = (
        Ticket.objects
        .filter(closed_at__isnull=False, closed_at__gte=months[0])
        .annotate(m=TruncMonth('closed_at'))
        .values('m')
        .annotate(count=Count('ticket_id'))
        .order_by('m')
    )
    closed_counts = align_counts(closed_qs)

    # Per priority created vs closed
    per_priority = {}
    for prio_key in [Ticket.NORMAL, Ticket.PRIORITY, Ticket.URGENT]:
        pr_created_qs = (
            Ticket.objects
            .filter(priority=prio_key, created_at__gte=months[0])
            .annotate(m=TruncMonth('created_at'))
            .values('m')
            .annotate(count=Count('ticket_id'))
            .order_by('m')
        )
        pr_closed_qs = (
            Ticket.objects
            .filter(priority=prio_key, closed_at__isnull=False, closed_at__gte=months[0])
            .annotate(m=TruncMonth('closed_at'))
            .values('m')
            .annotate(count=Count('ticket_id'))
            .order_by('m')
        )
        per_priority[prio_key] = {
            'created': align_counts(pr_created_qs),
            'closed': align_counts(pr_closed_qs),
        }

    # Average response time per month per priority (use closed_at month)
    avg_expr = Coalesce(
        'resolution_time',
        ExpressionWrapper(F('closed_at') - F('created_at'), output_field=DurationField())
    )
    avg_by_month_priority_qs = (
        Ticket.objects
        .filter(status=Ticket.CLOSED, closed_at__isnull=False, closed_at__gte=months[0])
        .annotate(m=TruncMonth('closed_at'))
        .values('m', 'priority')
        .annotate(avg_duration=Avg(avg_expr))
    )
    # Build nested mapping {(month_date, priority): hours_float}
    avg_map = {}
    for row in avg_by_month_priority_qs:
        td = row['avg_duration']
        hours = float(td.total_seconds()) / 3600.0 if td else 0.0
        avg_map[(row['m'].date(), row['priority'])] = round(hours, 2)

    avg_response_per_month = {
        Ticket.NORMAL: [],
        Ticket.PRIORITY: [],
        Ticket.URGENT: [],
    }
    for m in months:
        d = m.date()
        for pr in avg_response_per_month.keys():
            avg_response_per_month[pr].append(avg_map.get((d, pr), 0.0))

    # Prepare JSON-safe payloads for charts
    charts_payload = {
        'labels': chart_labels,
        'created': created_counts,
        'closed': closed_counts,
        'per_priority': {
            'normal': per_priority[Ticket.NORMAL],
            'priority': per_priority[Ticket.PRIORITY],
            'urgent': per_priority[Ticket.URGENT],
        },
        'avg_hours_per_month': {
            'normal': avg_response_per_month[Ticket.NORMAL],
            'priority': avg_response_per_month[Ticket.PRIORITY],
            'urgent': avg_response_per_month[Ticket.URGENT],
        },
    }
    charts_json = json.dumps(charts_payload)

    context = {
        'counts': counts,
        'recent_tickets': recent_tickets,
        'avg_by_priority': avg_by_priority_display,
        'charts_json': charts_json,
    }

    return render(request, 'tickets/dashboard.html', context)

def create_ticket(request):
    """View for creating a new ticket"""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                if not ticket.requester_name:
                    ticket.requester_name = request.user.get_full_name() or request.user.username
                if not ticket.requester_email:
                    ticket.requester_email = request.user.email
            ticket.save()
            # Send confirmation email
            send_ticket_confirmation_email(ticket)
            # Send notification to technical support
            try:
                send_ticket_to_support_email(ticket)
            except Exception as e:
                # No interrumpir el flujo si falla el correo a soporte
                messages.warning(request, f'El ticket fue creado, pero no se pudo notificar a soporte: {str(e)}')
            messages.success(request, f'Su ticket se ha enviado correctamente. Su ID de ticket es {ticket.ticket_id}')
            return redirect('ticket_detail', ticket_id=ticket.ticket_id)
    else:
        form = TicketForm(user=request.user)
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


@login_required
def tickets_list(request):
    """Listado general de tickets para el personal (con paginación y botón de detalle)."""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('home')

    tickets_qs = Ticket.objects.all().order_by('-created_at')

    # Paginación
    page_number = request.GET.get('page') or 1
    paginator = Paginator(tickets_qs, 20)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'tickets': page_obj.object_list,
        'title': 'Listado de Tickets',
    }

    return render(request, 'tickets/tickets_list.html', context)

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

def send_ticket_to_support_email(ticket):
    """Envía por correo al soporte técnico la información del ticket recién creado."""
    support_email = getattr(settings, 'SUPPORT_EMAIL', None)
    if not support_email:
        # No hay correo de soporte configurado; salir silenciosamente
        return

    # Construir URL del ticket
    ticket_url = reverse('ticket_detail', kwargs={'ticket_id': ticket.ticket_id})
    absolute_url = f"{settings.SITE_URL}{ticket_url}" if hasattr(settings, 'SITE_URL') else ticket_url

    # Permitir múltiples correos separados por coma
    if isinstance(support_email, str):
        recipients = [e.strip() for e in support_email.split(',') if e.strip()]
    else:
        recipients = list(support_email)

    subject = f"Nuevo Ticket #{ticket.ticket_id} — {ticket.subject}"

    html_message = render_to_string('tickets/emails/ticket_new_support.html', {
        'ticket': ticket,
        'ticket_url': absolute_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
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
