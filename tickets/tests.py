from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from .models import Ticket, TicketComment
from .views import send_ticket_assigned_email


def create_ticket(requester_email='cliente@test.com', with_attachment=True):
    attachment = None
    if with_attachment:
        attachment = SimpleUploadedFile(
            'prueba.pdf', b'contenido-del-pdf', content_type='application/pdf'
        )
    return Ticket.objects.create(
        subject='Problema con el sistema',
        description='Detalle de la solicitud de prueba',
        requester_name='Cliente Prueba',
        requester_email=requester_email,
        attachment=attachment,
    )


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class TicketEmailAttachmentTests(TestCase):
    """Verifica que en los correos el adjunto se muestre como botón y no la URL."""

    def assert_attachment_shown_as_button(self, template, context):
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags

        html = render_to_string(template, context)
        # El botón con el texto requerido existe
        self.assertIn('>Ver Archivo Adjunto<', html)
        # La URL del adjunto no se muestra como texto visible
        visible_text = strip_tags(html)
        self.assertNotIn('/media/', visible_text)
        self.assertNotIn('prueba.pdf', visible_text)

    def test_templates_show_button_instead_of_url(self):
        staff = User.objects.create_user(
            username='staff1', email='staff1@test.com', password='pass123', is_staff=True
        )
        ticket = create_ticket()
        comment = TicketComment.objects.create(
            ticket=ticket, author_name='Staff', content='Avance en el ticket'
        )

        base_context = {
            'ticket': ticket,
            'ticket_url': 'http://testserver/tickets/{}/'.format(ticket.ticket_id),
            'old_status': 'Abierto',
            'new_status': 'En Proceso',
            'resolution_time_str': '1 hora',
            'comment': comment,
            'assigned_user': staff,
        }
        templates = [
            'tickets/emails/ticket_confirmation.html',
            'tickets/emails/ticket_new_support.html',
            'tickets/emails/ticket_update.html',
            'tickets/emails/ticket_closed.html',
            'tickets/emails/ticket_status_change.html',
            'tickets/emails/ticket_assigned.html',
        ]
        for template in templates:
            with self.subTest(template=template):
                self.assert_attachment_shown_as_button(template, base_context)

    def test_attachment_section_hidden_when_no_attachment(self):
        from django.template.loader import render_to_string

        ticket = create_ticket(with_attachment=False)
        html = render_to_string('tickets/emails/ticket_confirmation.html', {
            'ticket': ticket,
            'ticket_url': 'http://testserver/',
        })
        self.assertNotIn('Archivo Adjunto', html)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AssignTicketEmailTests(TestCase):
    """Verifica que al asignar un ticket se notifique por correo al staff."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin', email='admin@test.com', password='pass123'
        )
        self.staff = User.objects.create_user(
            username='staff1', email='staff1@test.com', password='pass123', is_staff=True
        )
        self.ticket = create_ticket()

    def test_send_ticket_assigned_email_function(self):
        send_ticket_assigned_email(self.ticket, self.staff)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.staff.email, message.to)
        self.assertIn('asignado', message.subject.lower())
        self.assertIn(self.ticket.subject, message.body)
        self.assertIn('Ver Archivo Adjunto', message.body)

    def test_assign_ticket_view_notifies_assigned_user(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.post(
            reverse('assign_ticket', kwargs={'ticket_id': self.ticket.ticket_id}),
            {'user_id': self.staff.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.staff.email, message.to)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.staff)
        self.assertEqual(self.ticket.status, Ticket.IN_PROCESS)

    def test_assign_ticket_success_response_mentions_user(self):
        self.client.login(username='admin', password='pass123')
        response = self.client.post(
            reverse('assign_ticket', kwargs={'ticket_id': self.ticket.ticket_id}),
            {'user_id': self.staff.id},
        )
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn(self.staff.username, data['message'])

    def test_ticket_detail_update_form_notifies_new_assigned_user(self):
        """Asignar un ticket desde 'Actualizar Ticket' debe notificar al usuario asignado."""
        self.client.login(username='admin', password='pass123')
        response = self.client.post(
            reverse('ticket_detail', kwargs={'ticket_id': self.ticket.ticket_id}),
            {
                'update_submit': '1',
                'status': self.ticket.status,
                'priority': self.ticket.priority,
                'assigned_to': self.staff.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn(self.staff.email, message.to)
        self.assertIn(self.ticket.subject, message.subject)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.staff)

    def test_ticket_detail_update_no_duplicate_email_when_assignment_unchanged(self):
        """No enviar correo si el ticket ya estaba asignado al mismo usuario."""
        self.ticket.assigned_to = self.staff
        self.ticket.save()

        self.client.login(username='admin', password='pass123')
        response = self.client.post(
            reverse('ticket_detail', kwargs={'ticket_id': self.ticket.ticket_id}),
            {
                'update_submit': '1',
                'status': self.ticket.status,
                'priority': self.ticket.priority,
                'assigned_to': self.staff.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    def test_ticket_detail_update_notifies_when_reassigned(self):
        """Al reasignar a otro usuario se notifica al nuevo asignado."""
        other_staff = User.objects.create_user(
            username='staff2', email='staff2@test.com', password='pass123', is_staff=True
        )
        self.client.login(username='admin', password='pass123')
        response = self.client.post(
            reverse('ticket_detail', kwargs={'ticket_id': self.ticket.ticket_id}),
            {
                'update_submit': '1',
                'status': self.ticket.status,
                'priority': self.ticket.priority,
                'assigned_to': other_staff.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(other_staff.email, mail.outbox[0].to)
        self.assertNotIn(self.staff.email, mail.outbox[0].to)

        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, other_staff)
