"""
The category picker on the gallery forms.

It was a bare ``<select>``, which the browser draws in its own chrome: a
light-grey OS control sitting in a dark panel, with a native caret, and a
popup the browser sized to its own metrics — on a tablet it opened wider than
the card holding it. The control is now wrapped so the page can draw it, and
its unselected state says what it wants instead of showing a row of dashes.
"""
from django.test import TestCase
from django.urls import reverse

from apps.core.models import Category
from apps.gallery.forms import GalleryForm
from apps.gallery.models import Gallery
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


class CategoryPickerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='ایمپلنت')
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        self.client.login(username='doc', password=PASSWORD)

    def test_the_unselected_row_says_what_to_do(self):
        self.assertEqual(
            GalleryForm().fields['category'].empty_label,
            'یک دسته‌بندی انتخاب کنید',
        )

    def test_the_add_form_wraps_the_control(self):
        html = self.client.get(reverse('gallery:add_gallery')).content.decode()

        self.assertIn('gal-form__select', html)
        self.assertIn('یک دسته‌بندی انتخاب کنید', html)

    def test_the_update_form_wraps_it_too(self):
        gallery = Gallery.objects.create(category=self.category, doctor=self.user.doctor)

        html = self.client.get(
            reverse('gallery:update_gallery', kwargs={'pk': gallery.pk})
        ).content.decode()

        self.assertIn('gal-form__select', html)

    def test_every_category_is_still_an_option(self):
        Category.objects.create(name='ارتودنسی')

        options = list(GalleryForm().fields['category'].queryset)

        self.assertEqual(len(options), 2)
