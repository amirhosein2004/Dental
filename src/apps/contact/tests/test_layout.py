"""
Where the contact page puts each way of reaching the clinic.

The email used to be a fourth card in the row of practices — the same shape,
the same size, standing right beside them — so it read as a third location,
and it squeezed the two real addresses into two thirds of the row. It belongs
with the other written route to the clinic, beside the message form.
"""
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.about.models import About, Branch
from apps.about.tests.test_clinic_info import make_about


class ContactLayoutTests(TestCase):
    def setUp(self):
        cache.clear()
        self.about = make_about()
        Branch.objects.create(
            city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000', order=1,
        )
        Branch.objects.create(
            city='قوچان', address='خیابان گوهرشاد', phone='05147247247', order=2,
        )
        self.html = self.client.get(reverse('contact:contact')).content.decode()

    def test_the_practices_row_holds_only_practices(self):
        """Two cards for two cities — the email card is no longer among them."""
        self.assertEqual(self.html.count('class="ctc-branch"'), 2)
        self.assertNotIn('ctc-branch--email', self.html)

    def test_the_email_is_beside_the_message_form(self):
        self.assertIn('ctc-mail-card', self.html)
        self.assertIn(f'mailto:{self.about.email}', self.html)

    def test_the_page_still_offers_a_number_for_each_practice(self):
        self.assertIn('tel:05138000000', self.html)
        self.assertIn('tel:05147247247', self.html)


class ContactWithoutEmailTests(TestCase):
    """`About` may not exist yet on a fresh install."""

    def setUp(self):
        cache.clear()
        About.objects.all().delete()
        Branch.objects.create(city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000')

    def test_the_page_renders_without_an_email_card(self):
        response = self.client.get(reverse('contact:contact'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'ctc-mail-card')
