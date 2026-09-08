"""
Category management.

Categories are shared across blog and gallery, so there is no per-doctor
ownership here — any staff member may edit any of them. What has to hold is
that a visitor may not, and that deleting a category does not take the content
filed under it with it.
"""
import json

from django.test import TestCase
from django.urls import reverse

from apps.core.models import Category
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}


class CategoryAccessTests(TestCase):
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
        self.category = Category.objects.create(name='ایمپلنت')

    def _staff_urls(self):
        return [
            reverse('core:category'),
            reverse('core:add_category'),
            reverse('core:update_category', kwargs={'pk': self.category.pk}),
            reverse('core:remove_category', kwargs={'pk': self.category.pk}),
        ]

    def test_anonymous_gets_404_everywhere(self):
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_signed_in_patient_also_gets_404(self):
        self.client.login(username='patient', password=PASSWORD)
        for url in self._staff_urls():
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_a_doctor_sees_the_list(self):
        self.client.login(username='doc', password=PASSWORD)
        response = self.client.get(reverse('core:category'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ایمپلنت')

    def test_a_visitor_cannot_delete_a_category(self):
        self.client.post(
            reverse('core:remove_category', kwargs={'pk': self.category.pk}),
        )

        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class CategoryWriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        self.client.login(username='doc', password=PASSWORD)
        self.category = Category.objects.create(name='ایمپلنت')

    def test_a_doctor_can_add_a_category(self):
        self.client.post(reverse('core:add_category'), {'name': 'ارتودنسی'})

        self.assertTrue(Category.objects.filter(name='ارتودنسی').exists())

    def test_a_duplicate_name_is_refused(self):
        self.client.post(reverse('core:add_category'), {'name': 'ایمپلنت'})

        self.assertEqual(Category.objects.filter(name='ایمپلنت').count(), 1)

    def test_a_blank_name_is_refused(self):
        before = Category.objects.count()
        self.client.post(reverse('core:add_category'), {'name': ''})

        self.assertEqual(Category.objects.count(), before)

    def test_a_doctor_can_rename_a_category(self):
        self.client.post(
            reverse('core:update_category', kwargs={'pk': self.category.pk}),
            {'name': 'ایمپلنت فوری'},
        )

        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'ایمپلنت فوری')

    def test_a_doctor_can_delete_a_category(self):
        self.client.post(
            reverse('core:remove_category', kwargs={'pk': self.category.pk}),
        )

        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_delete_over_get_does_nothing(self):
        """
        A destructive action behind GET can be triggered by a prefetch or an
        <img> tag on any page the staff member happens to open.
        """
        self.client.get(
            reverse('core:remove_category', kwargs={'pk': self.category.pk}),
        )

        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())


class CategoryAjaxTests(TestCase):
    """
    The rename endpoint answers JSON when asked over AJAX and redirects
    otherwise. Both shapes are live, so both need pinning.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        self.client.login(username='doc', password=PASSWORD)
        self.category = Category.objects.create(name='ایمپلنت')

    def test_an_ajax_rename_returns_json(self):
        response = self.client.post(
            reverse('core:update_category', kwargs={'pk': self.category.pk}),
            {'name': 'ایمپلنت فوری'}, **AJAX,
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload['success'])
        self.assertEqual(payload['category_name'], 'ایمپلنت فوری')

    def test_an_ajax_rename_that_fails_returns_the_errors(self):
        Category.objects.create(name='ارتودنسی')

        response = self.client.post(
            reverse('core:update_category', kwargs={'pk': self.category.pk}),
            {'name': 'ارتودنسی'}, **AJAX,
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(json.loads(response.content)['success'])

    def test_a_plain_rename_still_redirects(self):
        response = self.client.post(
            reverse('core:update_category', kwargs={'pk': self.category.pk}),
            {'name': 'ایمپلنت فوری'},
        )

        self.assertRedirects(response, reverse('core:category'))


class CategoryContentTests(TestCase):
    """
    Categories are a shared taxonomy. Deleting one must not delete the posts
    and galleries filed under it — losing an article because someone tidied up
    a tag list is not a recoverable mistake.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor_user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def test_deleting_a_category_keeps_the_gallery(self):
        import io

        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image as PILImage

        from apps.dashboard.models import Doctor
        from apps.gallery.models import Gallery, Image

        buf = io.BytesIO()
        PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
        upload = SimpleUploadedFile('x.jpg', buf.getvalue(), content_type='image/jpeg')

        category = Category.objects.create(name='ایمپلنت')
        gallery = Gallery.objects.create(
            doctor=Doctor.objects.get(user=self.doctor_user), category=category,
        )
        Image.objects.create(gallery=gallery, image=upload)

        category.delete()

        gallery.refresh_from_db()
        self.assertIsNone(gallery.category, 'the gallery should survive uncategorised')
