"""
The gallery "load more" endpoint.

It previously returned raw JSON that the browser re-templated, and that copy
drifted from the redesigned markup until the button silently appended nothing.
These pin the contract: the endpoint returns rendered HTML carrying the current
CSS hooks, and paging walks the whole set without repeats or dead clicks.
"""
from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.gallery.models import Gallery, Image
from apps.gallery.views.public_view import GALLERY_PAGE_SIZE
from apps.users.models import CustomUser


AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='x.jpg'):
    buf = BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class GalleryLoadMoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='gdoc', email='g@x.test', first_name='گ', last_name='د',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.category = Category.objects.create(name='ایمپلنت')

        # 6 galleries -> two pages of 4 + 2.
        cls.galleries = []
        for i in range(6):
            gallery = Gallery.objects.create(doctor=cls.doctor, category=cls.category)
            Image.objects.create(gallery=gallery, image=tiny_jpeg(f'g{i}.jpg'))
            cls.galleries.append(gallery)

    def test_requires_ajax_header(self):
        resp = self.client.get(reverse('gallery:load_more_galleries'))
        self.assertEqual(resp.status_code, 400)

    def test_returns_rendered_tiles_not_raw_json_fields(self):
        resp = self.client.get(
            reverse('gallery:load_more_galleries'), {'offset': 4}, **AJAX
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data['count'], 2)
        self.assertFalse(data['has_more'])
        # Current design hooks — the old JSON contract had none of these.
        self.assertIn('gal-tile', data['html'])
        self.assertIn('gallery-swiper', data['html'])
        self.assertIn('--gal-span', data['html'])
        # Old Bootstrap markup must be gone.
        self.assertNotIn('col-md-6', data['html'])
        self.assertNotIn('gallery-box', data['html'])

    def setUp(self):
        # The list view caches whole responses for anonymous visitors, and
        # LocMemCache survives between tests in one process. A replayed cached
        # response carries no `.context`, so tests must start from a cold cache.
        cache.clear()

    def _page_all(self):
        """Walk first page + every "load more" page; return (tiles, rows)."""
        first = self.client.get(reverse('gallery:gallery_list'))
        tiles = len(first.context['galleries'])
        rows = first.context['next_offset']
        has_more = first.context['has_more']

        while has_more:
            data = self.client.get(
                reverse('gallery:load_more_galleries'), {'offset': rows}, **AJAX
            ).json()
            tiles += data['count']
            rows += data['consumed']
            has_more = data['has_more']
            if not data['consumed']:
                break  # guard against a paging bug spinning forever
        return tiles, rows

    def test_paging_covers_every_gallery_exactly_once(self):
        tiles, rows = self._page_all()
        self.assertEqual(tiles, 6)
        self.assertEqual(rows, 6)

    def test_empty_galleries_are_skipped_but_still_advance_offset(self):
        """
        An image-less gallery would render as a blank tile, so it is skipped —
        but the offset must still move past it or paging would re-request it
        forever. Asserted over the whole walk because `Gallery.Meta.ordering`
        is `-updated_at`, which puts a freshly created row on page one.
        """
        Gallery.objects.create(doctor=self.doctor, category=self.category)

        tiles, rows = self._page_all()
        self.assertEqual(tiles, 6)  # blank one not rendered
        self.assertEqual(rows, 7)   # but still consumed

    def test_admin_controls_only_for_permitted_users(self):
        # Pick a gallery that actually lands on the second page under the
        # model's own ordering, instead of assuming creation order.
        second_page = list(Gallery.objects.all()[GALLERY_PAGE_SIZE:])
        self.assertTrue(second_page)
        edit_url = reverse('gallery:update_gallery', args=[second_page[0].pk])

        anon = self.client.get(
            reverse('gallery:load_more_galleries'),
            {'offset': GALLERY_PAGE_SIZE}, **AJAX,
        ).json()
        self.assertNotIn(edit_url, anon['html'])

        self.client.login(username=self.user.username, password=PASSWORD)
        owner = self.client.get(
            reverse('gallery:load_more_galleries'),
            {'offset': GALLERY_PAGE_SIZE}, **AJAX,
        ).json()
        self.assertIn(edit_url, owner['html'])

    def test_no_dead_click_when_total_is_exact_multiple_of_page_size(self):
        """
        With 8 galleries and a page size of 4, the second page is the last one.
        `has_more` must already be False there — otherwise the user clicks a
        third time, nothing appends, and only then does the button vanish.
        """
        for i in range(2):  # 6 existing + 2 == 8
            extra = Gallery.objects.create(doctor=self.doctor, category=self.category)
            Image.objects.create(gallery=extra, image=tiny_jpeg(f'extra{i}.jpg'))
        self.assertEqual(Gallery.objects.count(), 2 * GALLERY_PAGE_SIZE)

        data = self.client.get(
            reverse('gallery:load_more_galleries'),
            {'offset': GALLERY_PAGE_SIZE}, **AJAX,
        ).json()
        self.assertEqual(data['count'], GALLERY_PAGE_SIZE)
        self.assertFalse(data['has_more'])

    def test_negative_offset_is_clamped(self):
        resp = self.client.get(
            reverse('gallery:load_more_galleries'), {'offset': '-5'}, **AJAX
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 4)

    def test_garbage_offset_falls_back_to_zero(self):
        resp = self.client.get(
            reverse('gallery:load_more_galleries'), {'offset': 'abc'}, **AJAX
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['count'], 4)


