"""
One treatment, one page.

Every service used to share `/service/`, so that single page was competing
with itself for "ایمپلنت", "ارتودنسی" and everything else at once. These tests
hold the split in place: a slug per treatment, a page that renders it, and a
list that actually links there.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.service.models import Service, ServiceFAQ
from apps.users.models import CustomUser


PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='x.jpg'):
    """A real (tiny) file, because `validate_image` reads the upload's size."""
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')



class ServiceSlugTests(TestCase):
    def test_the_slug_is_generated_from_the_persian_title(self):
        service = Service.objects.create(
            title='ایمپلنت دندان',
            description='کاشت ایمپلنت با متریال استاندارد و گارانتی کتبی.',
            image=tiny_jpeg(),
        )

        self.assertEqual(service.slug, 'ایمپلنت-دندان')

    def test_a_supplied_slug_is_kept(self):
        """Changing a slug breaks a URL Google already holds, so an explicit
        one is never overwritten."""
        service = Service.objects.create(
            title='لمینت سرامیکی',
            slug='laminate',
            description='لمینت سرامیکی برای طراحی لبخند، با حداقل تراش دندان.',
            image=tiny_jpeg(),
        )

        self.assertEqual(service.slug, 'laminate')

    def test_a_duplicate_title_still_produces_a_unique_slug(self):
        Service.objects.create(
            title='ونیر کامپوزیت',
            description='ونیر کامپوزیت برای اصلاح فرم و رنگ دندان‌های جلو.',
            image=tiny_jpeg(),
        )
        second = Service(
            title='ونیر کامپوزیت ',  # trailing space — a different title, same slug
            description='ونیر کامپوزیت برای اصلاح فرم و رنگ دندان‌های جلو.',
            image=tiny_jpeg(),
        )
        second.save()

        self.assertEqual(second.slug, 'ونیر-کامپوزیت-2')


class ServiceDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(
            title='ایمپلنت دندان',
            description='کاشت ایمپلنت با متریال استاندارد و گارانتی کتبی.',
            image=tiny_jpeg(),
        )
        cls.faq = ServiceFAQ.objects.create(
            service=cls.service,
            question='ایمپلنت چقدر طول می‌کشد؟',
            answer='بسته به وضعیت استخوان، بین سه تا شش ماه.',
        )

    def setUp(self):
        # Both the list and the detail view cache their data for a day.
        cache.clear()

    def test_the_page_renders(self):
        response = self.client.get(self.service.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ایمپلنت دندان')

    def test_an_unknown_slug_is_a_404(self):
        response = self.client.get('/service/چیزی-که-نیست/')

        self.assertEqual(response.status_code, 404)

    def test_the_staff_routes_still_win_over_the_slug_route(self):
        """
        `/service/add/` is declared before `<str:slug>`. Without that ordering
        it resolves as a service whose slug happens to be "add", and the staff
        who need the form get a 404 instead.

        Signed in, because an anonymous visitor gets 404 from the staff guard
        too — this project answers 404 rather than 403 so a probe cannot map
        the management routes by status code — and that 404 is
        indistinguishable from the one a missing slug produces.
        """
        CustomUser.objects.create_user(
            username='staff', email='staff@x.test', password=PASSWORD,
            first_name='سعیده', last_name='بابایی', is_doctor=True,
        )
        self.client.login(username='staff', password=PASSWORD)

        response = self.client.get(reverse('service:add_service'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'service/add_service.html')

    def test_the_faq_reaches_the_structured_data(self):
        body = self.client.get(self.service.get_absolute_url()).content.decode()

        self.assertIn('"@type": "FAQPage"', body)
        self.assertIn('ایمپلنت چقدر طول می‌کشد؟', body)

    def test_the_procedure_is_declared(self):
        body = self.client.get(self.service.get_absolute_url()).content.decode()

        self.assertIn('"@type": "MedicalProcedure"', body)

    def test_the_list_links_to_the_detail_page(self):
        """
        The grid is how a crawler reaches these pages in one hop. Without the
        link they exist only in the sitemap.
        """
        response = self.client.get(reverse('service:service_list'))

        self.assertContains(response, self.service.get_absolute_url())

    def test_the_description_falls_back_when_no_meta_is_set(self):
        """
        An empty meta description lets Google write its own snippet from
        whatever text it finds first, which here would be the navigation.
        """
        self.assertTrue(self.service.seo_description)
        self.assertIn('ایمپلنت', self.service.seo_description)
