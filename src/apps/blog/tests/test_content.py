"""
Blog content is the one field on the site rendered with ``|safe``, so these
tests are mostly about what must not survive a save.
"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.blog.models import BlogPost
from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='post.jpg'):
    buf = io.BytesIO()
    PILImage.new('RGB', (12, 12), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class BlogContentSanitisingTests(TestCase):
    """
    The CKEditor config lists script/iframe/style under ``htmlSupport.disallow``,
    but that only shapes what the editor emits. Anyone posting straight to the
    endpoint — or anyone using a phished doctor account — skips it, and the
    result runs in every visitor's browser. The model must be the filter.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor_user = CustomUser.objects.create_user(
            username='writer', email='w@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD, is_doctor=True,
        )
        cls.doctor = Doctor.objects.get(user=cls.doctor_user)
        cls.category = Category.objects.create(name='ایمپلنت')

    def _post(self, content, title='یک عنوان'):
        return BlogPost.objects.create(
            title=title,
            slug=title.replace(' ', '-'),
            content=content,
            writer=self.doctor,
            image=tiny_jpeg(),
        )

    def test_script_does_not_survive_a_save(self):
        body = 'متن سالم که به اندازه کافی بلند است تا از اعتبارسنجی طول عبور کند. ' * 2
        post = self._post(f'<p>{body}</p><script>alert(1)</script>')
        post.refresh_from_db()
        self.assertNotIn('<script', post.content)
        self.assertIn('متن سالم', post.content)

    def test_event_handler_does_not_survive_a_save(self):
        body = 'محتوای آزمایشی به قدر کافی طولانی برای عبور از اعتبارسنجی طول. ' * 2
        post = self._post(f'<p onmouseover="steal()">{body}</p>')
        post.refresh_from_db()
        self.assertNotIn('onmouseover', post.content)

    def test_sanitising_also_applies_on_update(self):
        body = 'محتوای اولیه که به اندازه کافی بلند است برای عبور از اعتبارسنجی. ' * 2
        post = self._post(f'<p>{body}</p>')
        post.content = f'<p>{body}</p><iframe src="//evil"></iframe>'
        post.save()
        post.refresh_from_db()
        self.assertNotIn('<iframe', post.content)

    def test_posted_script_is_gone_from_the_rendered_page(self):
        """End-to-end: through the real form, out through the real template."""
        self.client.login(username='writer', password=PASSWORD)
        body = 'یک مقاله واقعی درباره ایمپلنت دندان که طول کافی دارد. ' * 3

        response = self.client.post(reverse('blog:create_blog'), {
            'title': 'مقاله تست',
            'categories': [self.category.pk],
            'content': f'<p>{body}</p><script>alert("xss")</script>',
            'image': tiny_jpeg(),
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        post = BlogPost.objects.get(title='مقاله تست')
        detail = self.client.get(
            reverse('blog:blog_detail', kwargs={'slug': post.slug})
        )
        self.assertNotIn(b'<script>alert', detail.content)
