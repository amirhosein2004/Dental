"""
Upload limits.

Django caps the size of one file but never how many arrive together, so a
single multipart POST could hand the bucket thousands of images.
"""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.gallery.models import Gallery, Image
from apps.gallery.views.manage_view import MAX_IMAGES_PER_UPLOAD
from apps.users.models import CustomUser


AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='x.jpg'):
    buf = BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class UploadCapTests(TestCase):
    """
    Django limits the size of one uploaded file but never how many arrive
    together, so a single multipart POST could hand the bucket thousands of
    images — each validated, written and paid for before anything noticed.
    Staff-only, but selecting the wrong folder is a normal accident.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='updoc', email='u@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.category = Category.objects.create(name='ارتودنسی')

    def setUp(self):
        self.client.login(username='updoc', password=PASSWORD)

    def test_oversized_batch_is_refused_on_create(self):
        files = [tiny_jpeg(f'n{i}.jpg') for i in range(MAX_IMAGES_PER_UPLOAD + 1)]
        resp = self.client.post(reverse('gallery:add_gallery'), {
            'category': self.category.pk, 'image': files,
        })

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Gallery.objects.count(), 0)
        self.assertEqual(Image.objects.count(), 0)

    def test_batch_at_the_cap_is_accepted(self):
        files = [tiny_jpeg(f'y{i}.jpg') for i in range(MAX_IMAGES_PER_UPLOAD)]
        self.client.post(reverse('gallery:add_gallery'), {
            'category': self.category.pk, 'image': files,
        })

        self.assertEqual(Gallery.objects.count(), 1)
        self.assertEqual(Image.objects.count(), MAX_IMAGES_PER_UPLOAD)

    def test_oversized_batch_is_refused_when_appending(self):
        gallery = Gallery.objects.create(doctor=self.doctor, category=self.category)
        Image.objects.create(gallery=gallery, image=tiny_jpeg('first.jpg'))

        files = [tiny_jpeg(f'a{i}.jpg') for i in range(MAX_IMAGES_PER_UPLOAD + 1)]
        resp = self.client.post(
            reverse('gallery:add_gallery_images', kwargs={'pk': gallery.pk}),
            {'image': files},
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(gallery.images.count(), 1)  # nothing appended
