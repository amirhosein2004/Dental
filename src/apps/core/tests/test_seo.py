"""
The crawl surface: sitemap, robots.txt, canonical URLs and noindex.

Most of this is invisible when it breaks. A missing canonical does not raise,
a sitemap that silently drops a model returns 200, and a staff page that lost
its `noindex` looks identical in a browser — the cost shows up months later as
a duplicate in search results or a login form indexed under the practice's
name. Hence tests.
"""
import io

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.about.models import Branch
from apps.blog.models import BlogPost
from apps.dashboard.models import Doctor
from apps.service.models import Service
from apps.users.models import CustomUser


def tiny_jpeg(name='x.jpg'):
    """A real (tiny) file, because `validate_image` reads the upload's size."""
    buf = io.BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')



class RobotsTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_it_is_served_as_plain_text(self):
        response = self.client.get('/robots.txt')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain; charset=utf-8')

    def test_the_staff_areas_are_disallowed(self):
        body = self.client.get('/robots.txt').content.decode()

        self.assertIn('Disallow: /dashboard/', body)
        self.assertIn('Disallow: /auth/', body)

    def test_the_sitemap_is_advertised_absolutely(self):
        """
        A relative path here is ignored by crawlers, and the host differs
        between develop and production — which is why this is a view
        and not a static file.
        """
        body = self.client.get('/robots.txt').content.decode()

        self.assertIn('Sitemap: http://testserver/sitemap.xml', body)

    def test_the_admin_path_is_not_published(self):
        """
        robots.txt is the first file an attacker reads. Naming the secret
        admin path in it would hand it over.
        """
        from django.conf import settings

        body = self.client.get('/robots.txt').content.decode()

        self.assertNotIn(settings.SECURE_ADMIN_PANEL, body)


class SitemapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.service = Service.objects.create(
            title='ارتودنسی نامرئی',
            description='ارتودنسی با پلاک شفاف، بدون سیم و براکت فلزی.',
            image=tiny_jpeg(),
        )
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', password='pw-for-tests-1',
            first_name='سعیده', last_name='بابایی', is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=user)
        # A post, because the blog section of the sitemap is the one that
        # broke: Django's Sitemap calls `get_absolute_url()` by name, BlogPost
        # did not have one, and the AttributeError took down the whole file —
        # service and doctor URLs included. An empty blog hid that entirely.
        cls.post = BlogPost.objects.create(
            writer=cls.doctor,
            title='مراقبت از دندان پس از ایمپلنت',
            slug='مراقبت-پس-از-ایمپلنت',
            content='<p>' + ('متن آزمایشی مقاله برای تست. ' * 5) + '</p>',
            image=tiny_jpeg('post.jpg'),
        )

    def setUp(self):
        # /sitemap.xml is wrapped in `cache_page`, and the test cache is
        # local-memory shared across the run — without this, one test's
        # sitemap is served to the next.
        cache.clear()

    def test_it_renders(self):
        response = self.client.get('/sitemap.xml')

        self.assertEqual(response.status_code, 200)

    def test_it_lists_the_service_and_doctor_pages(self):
        body = self.client.get('/sitemap.xml').content.decode()

        self.assertIn(self.service.get_absolute_url(), body)
        self.assertIn(self.doctor.get_absolute_url(), body)

    def test_it_lists_blog_posts(self):
        """
        One section raising takes the whole sitemap with it, so this covers
        more than the blog: it is the only test where a post exists at all.
        """
        body = self.client.get('/sitemap.xml').content.decode()

        self.assertIn(self.post.get_absolute_url(), body)

    def test_it_omits_staff_pages(self):
        body = self.client.get('/sitemap.xml').content.decode()

        self.assertNotIn('/dashboard/', body)
        self.assertNotIn('/auth/', body)

    def test_an_unpublished_doctor_is_dropped(self):
        self.doctor.is_published = False
        self.doctor.save()

        body = self.client.get('/sitemap.xml').content.decode()

        self.assertNotIn(self.doctor.get_absolute_url(), body)

    def test_lastmod_is_the_rows_own_timestamp(self):
        """
        A sitemap that reports today for every URL teaches the crawler to
        ignore the field, which costs exactly the benefit it was added for.
        """
        body = self.client.get('/sitemap.xml').content.decode()

        self.assertIn(self.service.updated_at.date().isoformat(), body)


class CanonicalTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_every_page_declares_one(self):
        response = self.client.get(reverse('home:home'))

        self.assertContains(response, 'rel="canonical"')

    def test_the_query_string_is_excluded(self):
        """
        `/blog/`, `/blog/?page=1` and `/blog/?utm_source=x` are one page to a
        reader and three to a crawler; the ranking would divide between them.
        """
        response = self.client.get(reverse('blog:blog_list'), {'utm_source': 'telegram'})

        self.assertContains(response, 'rel="canonical" href="http://testserver/blog/"')
        self.assertNotContains(response, 'utm_source')


class NoIndexTests(TestCase):
    def setUp(self):
        cache.clear()

    """
    Staff pages must carry `noindex`. The robots.txt `Disallow` is not a
    substitute: a disallowed URL can still be listed, titled from an inbound
    link, precisely because the crawler never fetched the page to read a tag.
    """

    def test_the_login_page_is_noindexed(self):
        response = self.client.get(reverse('accounts:doctor_login'))

        self.assertContains(response, 'noindex')

    def test_public_pages_are_not(self):
        response = self.client.get(reverse('home:home'))

        self.assertContains(response, 'index, follow')
        self.assertNotContains(response, 'noindex')


class OrganizationStructuredDataTests(TestCase):
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

    def setUp(self):
        # The footer's branch list comes from a cached context processor.
        cache.clear()

    def test_both_practices_are_emitted(self):
        """
        Two nodes rather than one with two addresses: they have separate phone
        numbers, and `address` is single-valued.
        """
        body = self.client.get(reverse('home:home')).content.decode()

        self.assertIn('مشهد، خیابان نمونه، پلاک ۱', body)
        self.assertIn('قوچان، خیابان نمونه، پلاک ۲', body)

    def test_online_booking_is_declared(self):
        """
        The competitive claim. Appointments have always been bookable here;
        nothing on the page said so in a form a crawler reads.
        """
        body = self.client.get(reverse('home:home')).content.decode()

        self.assertIn('"@type": "ReserveAction"', body)

    def test_both_addresses_are_in_the_footer_of_every_page(self):
        """
        Site-wide, not only on the contact page — the repeated name/address/
        phone is what ties the site to each location.
        """
        body = self.client.get(reverse('blog:blog_list')).content.decode()

        self.assertIn(self.mashhad.address, body)
        self.assertIn(self.quchan.address, body)


class BranchTests(TestCase):
    def test_display_order_decides_which_branch_stands_in_for_the_site(self):
        """
        There is no "main practice" flag any more — the term named nothing a
        visitor ever sees. Wherever the site needs exactly one branch (the
        single call button in the shared CTA block) it takes the first by
        display order, which staff control by reordering.
        """
        Branch.objects.create(
            city='مشهد', address='آدرس یک', phone='05138000000', order=2,
        )
        second = Branch.objects.create(
            city='قوچان', address='آدرس دو', phone='05147000000', order=1,
        )

        self.assertEqual(Branch.get_primary(), second)

    def test_the_display_title_defaults_to_the_city(self):
        branch = Branch.objects.create(
            city='مشهد', address='آدرس', phone='05138000000',
        )

        self.assertEqual(branch.display_title, 'مطب دندانپزشکی مشهد')
