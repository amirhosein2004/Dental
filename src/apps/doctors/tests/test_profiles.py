"""
The public doctor profiles.

These pages exist because visitors search the doctors by name and, before
them, no page on this site carried a full name for that search to match. The
first two tests below are that claim written down: the name has to be in the
title and in the body, or the page has not done the one job it was added for.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.about.models import Branch
from apps.dashboard.models import Doctor
from apps.service.models import Service
from apps.users.models import CustomUser


def tiny_jpeg(name='x.jpg'):
    """A real (tiny) file, because `validate_image` reads the upload's size."""
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')



class DoctorProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='saeedeh', email='s@x.test', password='pw-for-tests-1',
            first_name='سعیده', last_name='بابایی', is_doctor=True,
        )
        # The dashboard signal creates the Doctor row on the is_doctor flag.
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.doctor.headline = 'دندانپزشک، متخصص ایمپلنت'
        cls.doctor.specialty = 'ایمپلنت و جراحی'
        cls.doctor.license_number = '۱۲۳۴۵'
        cls.doctor.education = 'دکترای دندانپزشکی — دانشگاه مشهد\nدوره ایمپلنت'
        cls.doctor.description = 'معرفی کامل پزشک برای صفحه رزومه، با متن به اندازه کافی بلند.'
        cls.doctor.save()

    def setUp(self):
        cache.clear()

    def test_the_slug_comes_from_the_doctors_name(self):
        """Persian, not transliterated — the URL should match what people type."""
        self.assertEqual(self.doctor.slug, 'سعیده-بابایی')

    def test_the_page_carries_the_full_name(self):
        """
        The reason the page exists. Surname alone was already on the site and
        was not enough to rank for "دکتر سعیده بابایی".
        """
        response = self.client.get(self.doctor.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'دکتر سعیده بابایی')

    def test_credentials_reach_the_structured_data(self):
        """
        Registration number and specialty are what a YMYL page is judged on,
        so they have to be in the Physician block and not only in the prose.
        """
        response = self.client.get(self.doctor.get_absolute_url())
        body = response.content.decode()

        self.assertIn('"@type": "Physician"', body)
        self.assertIn('۱۲۳۴۵', body)
        self.assertIn('ایمپلنت و جراحی', body)

    def test_the_page_is_indexable(self):
        """The inverse of the staff pages: this one must NOT be noindexed."""
        response = self.client.get(self.doctor.get_absolute_url())

        self.assertContains(response, 'index, follow')
        self.assertNotContains(response, 'noindex')

    def test_the_canonical_url_has_no_query_string(self):
        """
        `?utm_source=…` on a shared link must not mint a second address for
        the same profile.
        """
        response = self.client.get(
            self.doctor.get_absolute_url(), {'utm_source': 'instagram'}
        )

        self.assertContains(response, f'rel="canonical" href="http://testserver{self.doctor.get_absolute_url()}"')

    def test_an_unpublished_profile_is_gone_not_moved(self):
        """
        404 rather than a redirect: a redirect would hand the profile's
        accumulated ranking to whatever it pointed at, and a profile is
        normally unpublished because it is half-written.
        """
        self.doctor.is_published = False
        self.doctor.save()

        response = self.client.get(self.doctor.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_a_second_doctor_with_the_same_name_gets_its_own_slug(self):
        other = CustomUser.objects.create_user(
            username='saeedeh2', email='s2@x.test', password='pw-for-tests-1',
            first_name='سعیده', last_name='بابایی', is_doctor=True,
        )
        doctor = Doctor.objects.get(user=other)

        self.assertNotEqual(doctor.slug, self.doctor.slug)

    def test_the_list_page_links_every_profile(self):
        """
        The hub is how a crawler reaches the profiles in one hop. Without the
        link they are discoverable only through the sitemap.
        """
        response = self.client.get(reverse('doctors:doctor_list'))

        self.assertContains(response, self.doctor.get_absolute_url())


class DoctorBranchTests(TestCase):
    """A doctor's page shows where that doctor actually works."""

    @classmethod
    def setUpTestData(cls):
        cls.mashhad = Branch.objects.create(
            city='مشهد', address='مشهد، خیابان نمونه، پلاک ۱',
            phone='05138000000',
        )
        cls.quchan = Branch.objects.create(
            city='قوچان', address='قوچان، خیابان نمونه، پلاک ۲',
            phone='05147000000',
        )
        user = CustomUser.objects.create_user(
            username='sajjad', email='j@x.test', password='pw-for-tests-1',
            first_name='سجاد', last_name='بهمدی', is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=user)
        cls.doctor.description = 'معرفی کامل پزشک برای صفحه رزومه، با متن به اندازه کافی بلند.'
        cls.doctor.save()
        cls.doctor.branches.add(cls.mashhad)

    def setUp(self):
        cache.clear()

    def test_only_the_doctors_own_branch_is_shown(self):
        response = self.client.get(self.doctor.get_absolute_url())

        self.assertContains(response, self.mashhad.address)
        self.assertNotContains(response, self.quchan.address)

    def test_services_link_to_their_own_pages(self):
        """
        Internal linking, and the route out of a name search: someone who came
        for the doctor leaves for the treatment they actually need.
        """
        service = Service.objects.create(
            title='ایمپلنت دندان',
            description='کاشت ایمپلنت دندان با متریال استاندارد و گارانتی.',
            image=tiny_jpeg(),
        )
        self.doctor.services.add(service)

        response = self.client.get(self.doctor.get_absolute_url())

        self.assertContains(response, service.get_absolute_url())
