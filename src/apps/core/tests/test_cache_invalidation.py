"""
Cache invalidation.

Public pages are cached for a day. That is only safe if every write that could
change a page bumps that page's group — and the failure is silent: the site
keeps serving yesterday's content with nothing in the logs to say why.

The map lives in `core/signals.py`. These tests exist because reading it tells
you which models are wired, not which ones *should* be.
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
from apps.pricing.models import PricingCategory, PricingItem
from apps.service.models import Service
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
DESCRIPTION = 'توضیح آزمایشی برای این خدمت که به اندازه کافی طولانی است.'


def tiny_jpeg(name='x.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class InvalidationTests(TestCase):
    """
    Each test warms a page, writes something that changes it, and asks for the
    page again. A stale answer means the write did not reach the cache group.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.category = Category.objects.create(name='ایمپلنت')

    def setUp(self):
        cache.clear()

    # ------------------------------------------------------------ services --
    def test_a_new_service_appears_on_home_and_services(self):
        for url in (reverse('home:home'), reverse('service:service_list')):
            self.client.get(url)

        Service.objects.create(
            title='ایمپلنت فوری', description=DESCRIPTION, image=tiny_jpeg(),
        )

        self.assertContains(self.client.get(reverse('service:service_list')), 'ایمپلنت فوری')
        titles = [s.title for s in self.client.get(reverse('home:home')).context['services']]
        self.assertIn('ایمپلنت فوری', titles)

    # --------------------------------------------------------------- blog --
    def test_a_new_post_appears_on_home_and_blog(self):
        self.client.get(reverse('home:home'))
        self.client.get(reverse('blog:blog_list'))

        BlogPost.objects.create(
            title='مقاله تازه', slug='mghale-taze',
            content='متن آزمایشی مقاله که برای عبور از اعتبارسنجی طول کافی بلند است. ' * 2,
            writer=self.doctor, image=tiny_jpeg(),
        )

        self.assertContains(self.client.get(reverse('blog:blog_list')), 'مقاله تازه')
        titles = [b.title for b in self.client.get(reverse('home:home')).context['blogs']]
        self.assertIn('مقاله تازه', titles)

    # ------------------------------------------------------------ pricing --
    def test_a_new_tariff_appears_on_pricing(self):
        self.client.get(reverse('pricing:pricing_list'))

        pricing_category = PricingCategory.objects.create(name='جراحی', order=1)
        PricingItem.objects.create(
            category=pricing_category, title='کشیدن دندان عقل', price=3_000_000,
        )

        self.assertContains(
            self.client.get(reverse('pricing:pricing_list')), 'کشیدن دندان عقل',
        )

    # ------------------------------------------------------------ gallery --
    def test_a_new_gallery_appears_on_gallery_and_home(self):
        self.client.get(reverse('gallery:gallery_list'))
        self.client.get(reverse('home:home'))

        gallery = Gallery.objects.create(doctor=self.doctor, category=self.category)
        Image.objects.create(gallery=gallery, image=tiny_jpeg('new.jpg'))

        listed = self.client.get(reverse('gallery:gallery_list')).context['galleries']
        self.assertEqual(len(list(listed)), 1)

        on_home = self.client.get(reverse('home:home')).context['galleries']
        self.assertEqual(len(list(on_home)), 1)

    def test_adding_an_image_to_an_existing_gallery_refreshes_home(self):
        """
        The home page renders up to three images per gallery tile. Adding a
        fourth image changes what it shows, so `Image` has to bust `home` —
        not only `gallery`, which is all it used to do.
        """
        gallery = Gallery.objects.create(doctor=self.doctor, category=self.category)
        Image.objects.create(gallery=gallery, image=tiny_jpeg('one.jpg'))

        self.client.get(reverse('home:home'))          # warm

        Image.objects.create(gallery=gallery, image=tiny_jpeg('two.jpg'))

        shown = self.client.get(reverse('home:home')).context['galleries'][0]
        self.assertEqual(
            shown.images.count(), 2,
            'home served a cached copy that predates the new image',
        )

    # ------------------------------------------------------------- doctor --
    def test_renaming_a_doctor_refreshes_home_and_about(self):
        """
        The doctor's name and photo live on `CustomUser`, not on `Doctor`, and
        both pages render them. Editing a profile through the dashboard writes
        the user row — which has to invalidate the same groups a Doctor write
        does.
        """
        self.client.get(reverse('home:home'))
        self.client.get(reverse('about:about'))

        self.user.first_name = 'مریم'
        self.user.save()

        home_doctors = self.client.get(reverse('home:home')).context['doctors']
        self.assertEqual(
            home_doctors[0].user.first_name, 'مریم',
            'home served a cached copy with the old name',
        )

        about_doctors = self.client.get(reverse('about:about')).context['doctors']
        self.assertEqual(about_doctors[0].user.first_name, 'مریم')

    # ------------------------------------------------------------ category --
    def test_renaming_a_category_refreshes_the_gallery_filter(self):
        self.client.get(reverse('gallery:gallery_list'))

        self.category.name = 'ایمپلنت فوری'
        self.category.save()

        self.assertContains(
            self.client.get(reverse('gallery:gallery_list')), 'ایمپلنت فوری',
        )


class CacheIsolationTests(TestCase):
    """
    The cached copy is built for an anonymous visitor. Handing it to signed-in
    staff would hide their management controls; the reverse would leak staff
    controls to the public.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()

    def test_staff_controls_never_reach_an_anonymous_visitor(self):
        self.client.login(username='doc', password=PASSWORD)
        self.client.get(reverse('blog:blog_list'))     # warm as staff
        self.client.logout()

        self.assertNotContains(self.client.get(reverse('blog:blog_list')), 'داشبورد')

    def test_an_anonymous_cached_page_is_not_served_to_staff(self):
        self.client.get(reverse('blog:blog_list'))     # warm as anonymous

        self.client.login(username='doc', password=PASSWORD)
        self.assertContains(self.client.get(reverse('blog:blog_list')), 'داشبورد')
