"""
Filtering the article list by author.

It was a free-text box matched with `icontains` against the writer's first
*or* last name, so "بابایی" worked, "دکتر بابایی" matched nothing at all, and
a typo returned an empty page that looked like the clinic had never published
anything. Only doctors can write here and there are a handful of them, so the
whole set fits in one picker where every option is guaranteed to return
something.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.blog.models import BlogPost
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
# `validate_length` on `content` wants at least 50 characters.
CONTENT = '<p>' + 'متن آزمایشی این مقاله که به اندازه کافی طولانی است. ' * 3 + '</p>'


def tiny_jpeg(name='x.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


def make_doctor(username, first, last):
    user = CustomUser.objects.create_user(
        username=username, email=f'{username}@x.test', first_name=first,
        last_name=last, password=PASSWORD, is_doctor=True,
    )
    return Doctor.objects.get(user=user)


class AuthorPickerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.babaei = make_doctor('babaei', 'سعیده', 'بابایی')
        cls.behmadi = make_doctor('behmadi', 'سجاد', 'بهمدی')
        BlogPost.objects.create(
            title='ایمپلنت فوری', slug='implant', writer=cls.babaei,
            content=CONTENT, image=tiny_jpeg(),
        )
        BlogPost.objects.create(
            title='ارتودنسی نامرئی', slug='ortho', writer=cls.behmadi,
            content=CONTENT, image=tiny_jpeg(),
        )

    def setUp(self):
        cache.clear()
        self.url = reverse('blog:blog_list')

    def test_every_doctor_is_an_option(self):
        html = self.client.get(self.url).content.decode()

        self.assertIn('blg-author__menu', html)
        self.assertIn('دکتر سعیده بابایی', html)
        self.assertIn('دکتر سجاد بهمدی', html)

    def test_it_is_not_a_native_select(self):
        """
        A bare `<select>` is painted in the browser's own chrome, so it
        showed as a white OS control inside the dark filter pill with its
        own caret beside ours.
        """
        html = self.client.get(self.url).content.decode()

        self.assertNotIn('<select', html)

    def test_picking_an_author_narrows_the_list(self):
        html = self.client.get(self.url, {'writer': self.babaei.pk}).content.decode()

        self.assertIn('ایمپلنت فوری', html)
        self.assertNotIn('ارتودنسی نامرئی', html)

    def test_no_choice_shows_everything(self):
        html = self.client.get(self.url, {'writer': ''}).content.decode()

        self.assertIn('ایمپلنت فوری', html)
        self.assertIn('ارتودنسی نامرئی', html)

    def test_the_chosen_author_stays_selected(self):
        html = self.client.get(self.url, {'writer': self.behmadi.pk}).content.decode()

        self.assertRegex(html, rf'value="{self.behmadi.pk}"\s+checked')

    def test_the_trigger_names_the_chosen_author(self):
        """The closed picker is all most readers see of the current filter."""
        html = self.client.get(self.url, {'writer': self.behmadi.pk}).content.decode()
        trigger = html[html.index('blg-author__trigger'):html.index('blg-author__menu')]

        self.assertIn('دکتر سجاد بهمدی', trigger)

    def test_the_trigger_reads_as_unfiltered_with_no_choice(self):
        html = self.client.get(self.url).content.decode()
        trigger = html[html.index('blg-author__trigger'):html.index('blg-author__menu')]

        self.assertIn('همه‌ی نویسندگان', trigger)

    def test_a_junk_value_does_not_500(self):
        """The pk arrives from a query string; anything can be in there."""
        response = self.client.get(self.url, {'writer': 'not-a-pk'})

        self.assertEqual(response.status_code, 200)

    def test_a_junk_value_reads_as_no_author_chosen(self):
        """
        `selected_writer` labels the trigger. A stale or hand-edited pk has
        to fall back to the unfiltered wording, not to an empty label.
        """
        html = self.client.get(self.url, {'writer': '999999'}).content.decode()
        trigger = html[html.index('blg-author__trigger'):html.index('blg-author__menu')]

        self.assertIn('همه‌ی نویسندگان', trigger)
