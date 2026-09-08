"""
The CV block on the doctor's dashboard.

``Doctor`` has carried the credential fields for a while — specialty, degree,
medical-council number, education, work history — and the public profile page
already rendered every one of them. None of them had a form. The only way to
fill any of it in was the Django admin, i.e. a superuser account, so on a real
install the page a search for the doctor's own name lands on shipped mostly
empty.
"""
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from apps.about.models import Branch
from apps.dashboard.models import Doctor
from apps.service.models import Service
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
DESCRIPTION = 'توضیح آزمایشی برای این پزشک که به اندازه کافی طولانی است.'


class ResumeFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='سجاد', last_name='بهمدی',
            password=PASSWORD, is_doctor=True,
        )
        # A `Doctor` row is created by signal the moment `is_doctor` is set.
        cls.doctor = Doctor.objects.get(user=user)
        cls.doctor.description = DESCRIPTION
        cls.doctor.save()

    def setUp(self):
        cache.clear()
        self.client.login(username='doc', password=PASSWORD)
        self.url = reverse('dashboard:dashboard_doctor', kwargs={'doctor_id': self.doctor.id})

    def _payload(self, **overrides):
        data = {
            'form_kind': 'resume',
            'headline': 'دندانپزشک، متخصص ارتودنسی',
            'specialty': 'ارتودنسی',
            'degree': 'دکترای تخصصی ارتودنسی',
            'license_number': '128456',
            'experience_years': 8,
            'education': 'دکترای دندانپزشکی — دانشگاه علوم پزشکی مشهد، ۱۳۹۱',
            'experience': 'کلینیک نمونه، ۱۳۹۵ تا ۱۳۹۹',
            'certifications': '',
            'memberships': '',
            'meta_description': '',
            'order': '',
            'is_published': 'on',
        }
        data.update(overrides)
        return data

    def test_the_form_is_on_the_dashboard(self):
        self.assertContains(self.client.get(self.url), 'رزومه و سوابق')

    def test_the_credentials_are_saved(self):
        self.client.post(self.url, self._payload())

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.specialty, 'ارتودنسی')
        self.assertEqual(self.doctor.license_number, '128456')

    def test_an_empty_order_box_is_accepted(self):
        """`order` has a model default, so leaving it blank must not fail."""
        self.client.post(self.url, self._payload(order=''))

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.order, 0)

    def test_each_line_becomes_its_own_item(self):
        self.client.post(self.url, self._payload(
            education='دکترای دندانپزشکی، ۱۳۹۱\nتخصص ارتودنسی، ۱۳۹۵',
        ))

        self.doctor.refresh_from_db()
        self.assertEqual(len(self.doctor.education_list), 2)

    def test_the_practices_a_doctor_works_at_can_be_chosen(self):
        branch = Branch.objects.create(
            city='مشهد', address='بلوار سجاد', phone='05138000000',
        )

        self.client.post(self.url, self._payload(branches=[branch.pk]))

        self.assertEqual(list(self.doctor.branches.all()), [branch])

    def test_saving_the_resume_leaves_the_profile_text_alone(self):
        """
        The two forms edit the same row. The resume form does not carry
        `description`, so submitting it must not blank the bio the profile
        card above is responsible for.
        """
        self.client.post(self.url, self._payload())

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.description, DESCRIPTION)

    def test_a_profile_submit_still_works_without_the_marker(self):
        """
        The profile form is the default branch, so a client that sends no
        `form_kind` — a script, an older page — keeps working.
        """
        self.client.post(self.url, {
            'first_name': 'سجاد', 'last_name': 'بهمدی',
            'username': 'doc', 'email': 'd@x.test',
            'description': 'متن معرفی تازه که به اندازه کافی طولانی است.',
        })

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.description, 'متن معرفی تازه که به اندازه کافی طولانی است.')

    def test_the_edits_reach_the_public_profile(self):
        self.client.post(self.url, self._payload(services=[]))

        self.assertContains(
            self.client.get(self.doctor.get_absolute_url()), 'ارتودنسی',
        )

    def test_a_doctor_cannot_unpublish_their_own_page(self):
        """
        The switch is not on their form at all, so a save that omits it —
        every save they make — must leave the page standing.
        """
        payload = self._payload()
        payload.pop('is_published')

        self.client.post(self.url, payload)

        self.doctor.refresh_from_db()
        self.assertTrue(self.doctor.is_published)


class ResumeSiteFieldTests(TestCase):
    """
    Whether the profile is public, where it sorts and what Google prints
    under its title are site-wide answers, not part of anyone's CV — so the
    doctor never sees them and the superuser owns them.

    They are dropped from the form rather than hidden in the template: a
    hidden field still posts, so a doctor saving their credentials would
    blank the meta text and switch their own page off.
    """

    SITE_FIELDS = ('meta_description', 'is_published', 'order')

    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='سجاد', last_name='بهمدی',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=user)
        cls.doctor.description = DESCRIPTION
        cls.doctor.meta_description = 'متن متای نوشته‌ی سوپرادمین'
        cls.doctor.order = 3
        cls.doctor.save()
        CustomUser.objects.create_superuser(
            username='boss', email='b@x.test', first_name='مدیر', last_name='سایت',
            password=PASSWORD,
        )

    def setUp(self):
        cache.clear()
        self.url = reverse('dashboard:dashboard_doctor', kwargs={'doctor_id': self.doctor.id})

    def _payload(self, **overrides):
        data = {'form_kind': 'resume', 'specialty': 'ارتودنسی'}
        data.update(overrides)
        return data

    def test_a_doctor_is_not_shown_the_site_fields(self):
        self.client.login(username='doc', password=PASSWORD)

        html = self.client.get(self.url).content.decode()

        for name in self.SITE_FIELDS:
            with self.subTest(field=name):
                self.assertNotIn(f'name="{name}"', html)

    def test_a_superuser_is_shown_the_site_fields(self):
        self.client.login(username='boss', password=PASSWORD)

        html = self.client.get(self.url).content.decode()

        for name in self.SITE_FIELDS:
            with self.subTest(field=name):
                self.assertIn(f'name="{name}"', html)

    def test_a_doctors_save_leaves_the_site_fields_alone(self):
        self.client.login(username='doc', password=PASSWORD)

        self.client.post(self.url, self._payload(
            meta_description='', order=99, is_published='',
        ))

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.meta_description, 'متن متای نوشته‌ی سوپرادمین')
        self.assertEqual(self.doctor.order, 3)
        self.assertTrue(self.doctor.is_published)

    def test_a_superuser_can_still_change_them(self):
        self.client.login(username='boss', password=PASSWORD)

        self.client.post(self.url, self._payload(
            meta_description='متن تازه', order=7,
        ))

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.meta_description, 'متن تازه')
        self.assertEqual(self.doctor.order, 7)
        self.assertFalse(self.doctor.is_published)  # unchecked box = off

    def test_nobody_is_asked_to_tick_specialties_any_more(self):
        """
        The service checkboxes decided which treatments this doctor performs
        — a catalogue-wide answer no page on the site reads, so filling it
        in changed nothing and leaving it empty looked unfinished.
        """
        for username in ('doc', 'boss'):
            with self.subTest(user=username):
                self.client.login(username=username, password=PASSWORD)
                html = self.client.get(self.url).content.decode()
                self.assertNotIn('name="services"', html)


class ResumeAccessTests(TestCase):
    """The CV is one doctor's own; nobody else edits it."""

    @classmethod
    def setUpTestData(cls):
        owner = CustomUser.objects.create_user(
            username='owner', email='o@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=owner)
        CustomUser.objects.create_user(
            username='other', email='x@x.test', first_name='ج', last_name='د',
            password=PASSWORD, is_doctor=True,
        )
        CustomUser.objects.create_user(
            username='patient', email='p@x.test', first_name='ز', last_name='م',
            password=PASSWORD,
        )

    def setUp(self):
        cache.clear()
        self.url = reverse('dashboard:dashboard_doctor', kwargs={'doctor_id': self.doctor.id})

    def _post(self):
        return self.client.post(self.url, {
            'form_kind': 'resume', 'specialty': 'ایمپلنت', 'order': '',
        })

    def test_another_doctor_cannot_edit_it(self):
        self.client.login(username='other', password=PASSWORD)

        self._post()

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.specialty, '')

    def test_a_patient_cannot_edit_it(self):
        self.client.login(username='patient', password=PASSWORD)

        self._post()

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.specialty, '')

    def test_an_anonymous_visitor_cannot_edit_it(self):
        self._post()

        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.specialty, '')


class ResumeLinkTests(TestCase):
    """
    The home page must lead to the CV.

    Its doctor cards showed a truncated bio and offered only a booking button,
    so the trailing "…" had nowhere to go — while the page carrying the full
    credentials is the one a search for the doctor's name is looking for.
    """

    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='سعیده', last_name='بابایی',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=user)
        cls.doctor.description = DESCRIPTION
        cls.doctor.save()

    def setUp(self):
        cache.clear()

    def test_the_home_page_links_to_each_doctors_cv(self):
        self.assertContains(
            self.client.get(reverse('home:home')), self.doctor.get_absolute_url(),
        )

    def test_the_section_leads_to_the_doctors_index(self):
        self.assertContains(
            self.client.get(reverse('home:home')), reverse('doctors:doctor_list'),
        )
