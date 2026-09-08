"""
The blog "load more" endpoint — same contract as the gallery's.

Lived in `gallery/tests.py` until now, purely because both endpoints were
written in one sitting.
"""
from io import BytesIO

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.blog.models import BlogPost
from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser


AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='x.jpg'):
    buf = BytesIO()
    PILImage.new('RGB', (10, 10), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class BlogLoadMoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='bdoc', email='b@x.test', first_name='ب', last_name='د',
            password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.user)
        cls.category = Category.objects.create(name='ارتودنسی')

        for i in range(5):
            post = BlogPost.objects.create(
                title=f'مقاله شماره {i}', slug=f'post-{i}', writer=cls.doctor,
                content='محتوای آزمایشی که باید از پنجاه کاراکتر بیشتر باشد تا اعتبارسنجی رد نشود.',
                image=tiny_jpeg(f'b{i}.jpg'),
            )
            post.categories.set([cls.category])

    def setUp(self):
        cache.clear()

    def test_requires_ajax_header(self):
        self.assertEqual(
            self.client.get(reverse('blog:load_more_blogs')).status_code, 400
        )

    def test_returns_rendered_cards_matching_current_design(self):
        resp = self.client.get(
            reverse('blog:load_more_blogs'), {'offset': 3}, **AJAX
        )
        data = resp.json()

        self.assertEqual(data['count'], 2)
        self.assertFalse(data['has_more'])
        self.assertIn('blg-post', data['html'])
        self.assertIn('blg-post__body', data['html'])
        # Pre-redesign Bootstrap markup must not come back.
        self.assertNotIn('card-img-top', data['html'])
        self.assertNotIn('col-sm-6', data['html'])

    def test_no_dead_click_when_total_is_exact_multiple_of_page_size(self):
        """6 posts / page size 3 => page two is the last; no third dead click."""
        post = BlogPost.objects.create(
            title='مقاله ششم', slug='post-6', writer=self.doctor,
            content='محتوای آزمایشی که باید از پنجاه کاراکتر بیشتر باشد تا اعتبارسنجی رد نشود.',
            image=tiny_jpeg('b6.jpg'),
        )
        post.categories.set([self.category])
        self.assertEqual(BlogPost.objects.count(), 6)

        data = self.client.get(
            reverse('blog:load_more_blogs'), {'offset': 3}, **AJAX
        ).json()
        self.assertEqual(data['count'], 3)
        self.assertFalse(data['has_more'])

    def test_appended_cards_are_never_the_feature_tile(self):
        """The oversized tile belongs to the first slot only."""
        data = self.client.get(
            reverse('blog:load_more_blogs'), {'offset': 3}, **AJAX
        ).json()
        self.assertNotIn('blg-post--feature', data['html'])

    def test_admin_controls_only_for_permitted_users(self):
        newest = BlogPost.objects.order_by('-updated_at')[3]
        edit_url = reverse('blog:update_blog', args=[newest.pk])

        anon = self.client.get(
            reverse('blog:load_more_blogs'), {'offset': 3}, **AJAX
        ).json()
        self.assertNotIn(edit_url, anon['html'])

        self.client.login(username=self.user.username, password=PASSWORD)
        owner = self.client.get(
            reverse('blog:load_more_blogs'), {'offset': 3}, **AJAX
        ).json()
        self.assertIn(edit_url, owner['html'])


