"""
DoctorForm's social fields.

Doctors type a bare handle; the form stores a full profile URL so every
template can use the value straight as an href. Lived in `gallery/tests.py`
until now.
"""
from django.test import TestCase

from apps.dashboard.forms import DoctorForm
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


class DoctorFormSocialTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='fdoc', email='f@x.test', first_name='ف', last_name='د',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)

    def test_form_saves_handle_as_url(self):

        form = DoctorForm(
            data={
                'description': 'توضیحات آزمایشی برای پزشک که کافی طولانی است.',
                'instagram': 'dr.babaei',
                'telegram': '@sbdental',
                'twitter': '',
                'linkedin': 'https://www.linkedin.com/in/dr-negar',
            },
            instance=self.doctor,
        )
        self.assertTrue(form.is_valid(), form.errors)
        doctor = form.save()

        self.assertEqual(doctor.instagram, 'https://instagram.com/dr.babaei')
        self.assertEqual(doctor.telegram, 'https://t.me/sbdental')
        self.assertEqual(doctor.twitter, '')
        self.assertEqual(doctor.linkedin, 'https://www.linkedin.com/in/dr-negar')

    def test_form_prefills_with_handle_not_url(self):

        self.doctor.instagram = 'https://instagram.com/dr.babaei'
        self.doctor.save()

        form = DoctorForm(instance=self.doctor)
        self.assertEqual(form.initial['instagram'], 'dr.babaei')

    def test_form_rejects_bad_handle(self):

        form = DoctorForm(
            data={
                'description': 'توضیحات آزمایشی برای پزشک که کافی طولانی است.',
                'instagram': 'not a handle',
            },
            instance=self.doctor,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('instagram', form.errors)
