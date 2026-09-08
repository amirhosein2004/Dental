"""
Who is shown the two SEO override boxes on the treatment form.

`meta_title` and `meta_description` overwrite what a search result shows.
`Service` builds both from the treatment's own title and blurb when they are
blank, which is the right answer nearly every time — so putting them in front
of every doctor offered a way to make the page worse and no way to make it
better. They are a superuser's tool now; the treatment's display order stays
with everyone, because that is an editorial choice about this site.
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


class SeoFieldVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        CustomUser.objects.create_superuser(
            username='boss', email='b@x.test', first_name='م', last_name='ن',
            password=PASSWORD,
        )

    def setUp(self):
        cache.clear()
        self.service = Service.objects.create(
            title='ایمپلنت', description=DESCRIPTION, image=tiny_jpeg(),
            meta_title='ایمپلنت دندان در مشهد',
            meta_description='توضیح متایی که سوپرادمین نوشته است.',
        )
        self.url = reverse('service:update_service', kwargs={'pk': self.service.pk})

    def test_a_doctor_is_not_shown_the_seo_boxes(self):
        self.client.login(username='doc', password=PASSWORD)

        response = self.client.get(self.url)

        self.assertNotContains(response, 'name="meta_title"')
        self.assertNotContains(response, 'name="meta_description"')

    def test_a_doctor_still_sets_the_display_order(self):
        self.client.login(username='doc', password=PASSWORD)

        self.assertContains(self.client.get(self.url), 'name="order"')

    def test_a_superuser_is_shown_the_seo_boxes(self):
        self.client.login(username='boss', password=PASSWORD)

        response = self.client.get(self.url)

        self.assertContains(response, 'name="meta_title"')
        self.assertContains(response, 'name="meta_description"')

    def test_a_doctors_edit_leaves_the_seo_text_alone(self):
        """
        The decisive one. Hiding the boxes with CSS — or with a hidden input —
        would have posted an empty value and wiped what a superuser wrote, on
        every unrelated edit. The fields are dropped from the form instead, so
        `construct_instance` never touches them.
        """
        self.client.login(username='doc', password=PASSWORD)

        self.client.post(self.url, {
            'title': 'ایمپلنت', 'description': DESCRIPTION,
            'content': '', 'order': 0,
        })

        self.service.refresh_from_db()
        self.assertEqual(self.service.meta_title, 'ایمپلنت دندان در مشهد')
        self.assertEqual(
            self.service.meta_description, 'توضیح متایی که سوپرادمین نوشته است.',
        )

    def test_a_superuser_can_still_change_them(self):
        self.client.login(username='boss', password=PASSWORD)

        self.client.post(self.url, {
            'title': 'ایمپلنت', 'description': DESCRIPTION, 'content': '',
            'meta_title': 'عنوان تازه', 'meta_description': 'توضیح تازه', 'order': 0,
        })

        self.service.refresh_from_db()
        self.assertEqual(self.service.meta_title, 'عنوان تازه')
