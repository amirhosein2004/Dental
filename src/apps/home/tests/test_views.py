"""
The home page.

It is the one page that reads from five apps at once, so the risks come from
that: falling over when a section has no rows yet, and serving a cached copy
of the anonymous page to signed-in staff.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.blog.models import BlogPost
from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.gallery.models import Gallery, Image
from apps.home.views.home_view import HomeView
from apps.service.models import Service
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
DESCRIPTION = 'توضیح آزمایشی برای این خدمت که به اندازه کافی طولانی است.'


def tiny_jpeg(name='x.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class EmptySiteTests(TestCase):
    """
    A brand-new deployment has no clinic profile, no doctors and no content.
    The home page is the first thing anyone opens, so it must render anyway
    rather than 500 on a missing row.
    """

    def setUp(self):
        cache.clear()

    def test_home_renders_with_no_data_at_all(self):
        response = self.client.get(reverse('home:home'))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['about'])
        self.assertEqual(list(response.context['doctors']), [])


class PreviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=user)
        cls.category = Category.objects.create(name='ایمپلنت')

        # Two more of each than the page shows, so a broken limit is visible.
        for i in range(HomeView.PREVIEW_SIZE + 2):
            Service.objects.create(
                title=f'خدمت {i}', description=DESCRIPTION, image=tiny_jpeg(f's{i}.jpg'),
            )
            BlogPost.objects.create(
                title=f'مقاله {i}', slug=f'post-{i}',
                content='متن آزمایشی مقاله که برای عبور از اعتبارسنجی طول کافی بلند است. ' * 2,
                writer=cls.doctor, image=tiny_jpeg(f'b{i}.jpg'),
            )
            gallery = Gallery.objects.create(doctor=cls.doctor, category=cls.category)
            Image.objects.create(gallery=gallery, image=tiny_jpeg(f'g{i}.jpg'))

    def setUp(self):
        cache.clear()

    def test_each_strip_is_capped_at_the_preview_size(self):
        response = self.client.get(reverse('home:home'))

        for key in ('services', 'blogs', 'galleries'):
            with self.subTest(section=key):
                self.assertEqual(len(list(response.context[key])), HomeView.PREVIEW_SIZE)

    def test_every_doctor_is_listed(self):
        """Doctors are not a teaser — the whole team belongs on the page."""
        response = self.client.get(reverse('home:home'))

        self.assertEqual(len(list(response.context['doctors'])), 1)


class CacheTests(TestCase):
    """
    The page is cached for a day under a key with no user segment, so the
    cached copy must never be handed to someone whose navbar differs.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()

    def test_a_new_service_appears_after_the_cache_is_invalidated(self):
        self.client.get(reverse('home:home'))          # warm the cache

        Service.objects.create(
            title='ایمپلنت فوری', description=DESCRIPTION, image=tiny_jpeg(),
        )

        response = self.client.get(reverse('home:home'))
        titles = [s.title for s in response.context['services']]
        self.assertIn('ایمپلنت فوری', titles, 'the cache was not invalidated on write')

    def test_staff_see_their_own_controls_not_the_anonymous_copy(self):
        anonymous = self.client.get(reverse('home:home'))
        self.assertNotContains(anonymous, 'داشبورد')

        self.client.login(username='doc', password=PASSWORD)
        signed_in = self.client.get(reverse('home:home'))
        self.assertContains(signed_in, 'داشبورد')
