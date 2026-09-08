"""
Services: the public list, and the three staff screens behind it.

The staff screens answer 404 rather than 403 to anyone who should not be
there — the same rule the rest of the site follows, so a probe cannot use the
status code to map which management routes exist.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.service.models import Service
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
DESCRIPTION = 'توضیح آزمایشی برای این خدمت که به اندازه کافی طولانی است.'


def tiny_jpeg(name='x.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class PublicListTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_the_list_renders_when_empty(self):
        response = self.client.get(reverse('service:service_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['services']), [])

    def test_services_are_listed(self):
        Service.objects.create(title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg())

        self.assertContains(self.client.get(reverse('service:service_list')), 'ایمپلنت')

    def test_a_new_service_is_not_hidden_by_the_cache(self):
        """The list is cached for a day; a write has to invalidate it."""
        self.client.get(reverse('service:service_list'))      # warm

        Service.objects.create(title='ارتودنسی', description=DESCRIPTION, image=tiny_jpeg())

        self.assertContains(self.client.get(reverse('service:service_list')), 'ارتودنسی')


class StaffAccessTests(TestCase):
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
        cache.clear()
        self.service = Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
        )

    def _staff_urls(self):
        return [
            reverse('service:add_service'),
            reverse('service:update_service', kwargs={'pk': self.service.pk}),
            reverse('service:remove_service', kwargs={'pk': self.service.pk}),
        ]

    def test_anonymous_gets_404_on_every_staff_screen(self):
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_signed_in_patient_also_gets_404(self):
        """Being logged in is not the same as being staff."""
        self.client.login(username='patient', password=PASSWORD)
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_doctor_can_create_a_service(self):
        self.client.login(username='doc', password=PASSWORD)
        self.client.post(reverse('service:add_service'), {
            'title': 'لمینت', 'description': DESCRIPTION, 'image': tiny_jpeg(),
        })

        self.assertTrue(Service.objects.filter(title='لمینت').exists())

    def test_a_doctor_can_delete_a_service(self):
        self.client.login(username='doc', password=PASSWORD)
        self.client.post(reverse('service:remove_service', kwargs={'pk': self.service.pk}))

        self.assertFalse(Service.objects.filter(pk=self.service.pk).exists())

    def test_a_visitor_cannot_delete_a_service(self):
        self.client.post(reverse('service:remove_service', kwargs={'pk': self.service.pk}))

        self.assertTrue(Service.objects.filter(pk=self.service.pk).exists())

    def test_a_file_that_is_not_an_image_is_refused(self):
        """Extension alone proves nothing; the validator opens the file."""
        self.client.login(username='doc', password=PASSWORD)
        self.client.post(reverse('service:add_service'), {
            'title': 'جعلی', 'description': DESCRIPTION,
            'image': SimpleUploadedFile('x.jpg', b'not an image', content_type='image/jpeg'),
        })

        self.assertFalse(Service.objects.filter(title='جعلی').exists())
