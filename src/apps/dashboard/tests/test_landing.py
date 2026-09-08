"""
What the dashboard looks like the moment it opens.
"""
from django.test import TestCase
from django.urls import reverse

from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


class DashboardAutofocusTests(TestCase):
    """
    Opening the dashboard must land on the dashboard.

    ``PasswordChangeForm`` ships ``autofocus=True`` on ``old_password`` — right
    for the standalone change-password page, wrong here: the security card is
    the fourth block down, and a browser honouring autofocus scrolls to it, so
    the page opened already past the hero, the profile and the CV.
    """

    @classmethod
    def setUpTestData(cls):
        # dashboard.signals creates the Doctor row from is_doctor=True.
        cls.user = CustomUser.objects.create_user(
            username='focusdoc', email='f@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )
        cls.doctor = cls.user.doctor

    def test_no_field_steals_focus_on_load(self):
        self.client.login(username='focusdoc', password=PASSWORD)
        response = self.client.get(
            reverse('dashboard:dashboard_doctor', kwargs={'doctor_id': self.doctor.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('autofocus', response.content.decode())

    def test_the_standalone_page_keeps_its_autofocus(self):
        """The dashboard is the exception; the dedicated page is not."""
        self.client.login(username='focusdoc', password=PASSWORD)
        response = self.client.get(
            reverse('accounts:change_password', kwargs={'user_id': self.user.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('autofocus', response.content.decode())
