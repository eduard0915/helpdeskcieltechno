from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from .forms import PasswordResetForm

# Los tests no dependen de collectstatic: usar el storage de estáticos simple.
TEST_STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}


class PasswordResetFormTests(TestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username='activo', email='activo@test.com', password='x', is_active=True
        )
        User.objects.create_user(
            username='inactivo', email='inactivo@test.com', password='x', is_active=False
        )

    def test_valid_email_for_active_user(self):
        form = PasswordResetForm(data={'email': 'activo@test.com'})
        self.assertTrue(form.is_valid())

    def test_email_is_case_insensitive(self):
        form = PasswordResetForm(data={'email': 'ACTIVO@TEST.COM'})
        self.assertTrue(form.is_valid())

    def test_nonexistent_email_is_rejected(self):
        form = PasswordResetForm(data={'email': 'no-existe@test.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('No existe ninguna cuenta registrada', str(form.errors))

    def test_inactive_user_is_rejected(self):
        form = PasswordResetForm(data={'email': 'inactivo@test.com'})
        self.assertFalse(form.is_valid())
        self.assertIn('inactiva', str(form.errors))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', STORAGES=TEST_STORAGES)
class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.active_user = User.objects.create_user(
            username='activo', email='activo@test.com', password='x', is_active=True
        )
        User.objects.create_user(
            username='inactivo', email='inactivo@test.com', password='x', is_active=False
        )

    def test_reset_with_valid_email_sends_mail(self):
        response = self.client.post(reverse('password_reset'), {'email': 'activo@test.com'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.active_user.email, mail.outbox[0].to)

    def test_reset_with_nonexistent_email_shows_error_and_sends_nothing(self):
        response = self.client.post(reverse('password_reset'), {'email': 'no-existe@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No existe ninguna cuenta registrada')
        self.assertEqual(len(mail.outbox), 0)

    def test_reset_with_inactive_user_shows_error_and_sends_nothing(self):
        response = self.client.post(reverse('password_reset'), {'email': 'inactivo@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inactiva')
        self.assertEqual(len(mail.outbox), 0)
