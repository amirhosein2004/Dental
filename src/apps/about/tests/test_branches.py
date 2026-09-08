"""
Staff CRUD for the practices.

Every one of these URLs edits data that renders in the footer of every page on
the site, so the access rule matters as much as the behaviour: 404 rather than
403 to anyone who should not be there, the same rule the rest of the staff
area follows, so a probe cannot use the status code to map which management
routes exist.
"""
from django.test import TestCase
from django.urls import reverse

from apps.about.context_processors import invalidate_about_info_cache
from apps.about.models import Branch
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


def branch_payload(**overrides):
    data = {
        'city': 'مشهد',
        'title': '',
        'address': 'بلوار سجاد، پلاک ۱',
        'postal_code': '',
        'phone': '05147247247',
        'extra_phones': '',
        'hours': '',
        'map_embed_url': '',
        'map_link': '',
        'latitude': '',
        'longitude': '',
        'order': 0,
    }
    data.update(overrides)
    return data


class BranchMapTests(TestCase):
    """
    One map per practice on the contact page.

    A single map centred between two cities 200km apart frames neither of
    them, and one marker cannot say which practice it is. Coordinates are
    optional, so a practice without them has to render an address and a search
    link rather than an empty grey box.
    """

    def setUp(self):
        invalidate_about_info_cache()

    def test_a_practice_with_coordinates_gets_a_map(self):
        Branch.objects.create(
            city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000',
            latitude='36.3165', longitude='59.5266',
        )

        response = self.client.get(reverse('contact:contact'))

        self.assertContains(response, 'data-map-lat="36.316500"')
        self.assertContains(response, 'data-map-lng="59.526600"')

    def test_both_practices_get_their_own_map(self):
        Branch.objects.create(
            city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000',
            latitude='36.3165', longitude='59.5266', order=1,
        )
        Branch.objects.create(
            city='قوچان', address='خیابان گوهرشاد', phone='05147247247',
            latitude='37.1068', longitude='58.5125', order=2,
        )

        html = self.client.get(reverse('contact:contact')).content.decode()

        self.assertEqual(html.count('data-map-lat='), 2)

    def test_a_practice_without_coordinates_gets_a_note_not_an_empty_box(self):
        Branch.objects.create(
            city='قوچان', address='خیابان گوهرشاد', phone='05147247247',
        )

        response = self.client.get(reverse('contact:contact'))

        self.assertNotContains(response, 'data-map-lat=')
        self.assertContains(response, 'مختصات این مطب هنوز ثبت نشده')

    def test_the_contact_page_names_every_practice(self):
        Branch.objects.create(
            city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000', order=1,
        )
        Branch.objects.create(
            city='قوچان', address='خیابان گوهرشاد', phone='05147247247', order=2,
        )

        response = self.client.get(reverse('contact:contact'))

        self.assertContains(response, 'بلوار وکیل‌آباد')
        self.assertContains(response, 'خیابان گوهرشاد')

    def test_each_practices_hours_are_on_the_contact_page(self):
        Branch.objects.create(
            city='مشهد', address='بلوار وکیل‌آباد', phone='05138000000',
            hours='شنبه تا چهارشنبه: ۹ تا ۱۳', order=1,
        )
        Branch.objects.create(
            city='قوچان', address='خیابان گوهرشاد', phone='05147247247',
            hours='شنبه تا چهارشنبه: ۱۶ تا ۲۰', order=2,
        )

        response = self.client.get(reverse('contact:contact'))

        self.assertContains(response, 'شنبه تا چهارشنبه: ۹ تا ۱۳')
        self.assertContains(response, 'شنبه تا چهارشنبه: ۱۶ تا ۲۰')


class BranchAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.patient = CustomUser.objects.create_user(
            username='patient', email='p@x.test', first_name='ز', last_name='م',
            password=PASSWORD,
        )

    def setUp(self):
        invalidate_about_info_cache()
        self.branch = Branch.objects.create(
            city='قوچان', address='خیابان اصلی', phone='05147247247',
        )

    def _staff_urls(self):
        return [
            reverse('about:branch_list'),
            reverse('about:branch_add'),
            reverse('about:branch_edit', kwargs={'pk': self.branch.pk}),
        ]

    def test_anonymous_gets_404_on_every_branch_screen(self):
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_signed_in_patient_also_gets_404(self):
        self.client.login(username='patient', password=PASSWORD)
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_doctor_reaches_every_branch_screen(self):
        self.client.login(username='doc', password=PASSWORD)
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_a_visitor_cannot_delete_a_branch(self):
        self.client.post(reverse('about:branch_delete', kwargs={'pk': self.branch.pk}))

        self.assertTrue(Branch.objects.filter(pk=self.branch.pk).exists())


class BranchWriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        invalidate_about_info_cache()
        self.client.login(username='doc', password=PASSWORD)

    def test_a_doctor_can_add_a_branch(self):
        self.client.post(reverse('about:branch_add'), branch_payload())

        self.assertTrue(Branch.objects.filter(city='مشهد').exists())

    def test_an_empty_order_box_is_accepted(self):
        """`order` has a model default, so leaving it blank must not fail."""
        self.client.post(reverse('about:branch_add'), branch_payload(order=''))

        self.assertEqual(Branch.objects.get(city='مشهد').order, 0)

    def test_a_doctor_can_edit_a_branch(self):
        branch = Branch.objects.create(
            city='قوچان', address='قدیمی', phone='05147247247',
        )

        self.client.post(
            reverse('about:branch_edit', kwargs={'pk': branch.pk}),
            branch_payload(city='قوچان', address='آدرس تازه'),
        )

        branch.refresh_from_db()
        self.assertEqual(branch.address, 'آدرس تازه')

    def test_a_doctor_can_delete_a_branch(self):
        branch = Branch.objects.create(
            city='قوچان', address='خیابان اصلی', phone='05147247247',
        )

        self.client.post(reverse('about:branch_delete', kwargs={'pk': branch.pk}))

        self.assertFalse(Branch.objects.filter(pk=branch.pk).exists())

    def test_delete_by_get_does_nothing(self):
        """A GET that deletes is one crawler visit away from wiping contacts."""
        branch = Branch.objects.create(
            city='قوچان', address='خیابان اصلی', phone='05147247247',
        )

        self.client.get(reverse('about:branch_delete', kwargs={'pk': branch.pk}))

        self.assertTrue(Branch.objects.filter(pk=branch.pk).exists())

    def test_a_new_branch_reaches_the_footer_immediately(self):
        """The context processor caches for six hours; a write must bust it."""
        self.client.get(reverse('about:branch_list'))      # warm

        self.client.post(reverse('about:branch_add'), branch_payload(city='نیشابور'))

        self.assertContains(self.client.get(reverse('home:home')), 'نیشابور')
