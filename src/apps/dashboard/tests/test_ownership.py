"""
Access-control matrix for doctor-owned content.

Contract under test:
  * superuser (doctor or not) -> full access to every dashboard, blog, gallery
  * doctor -> own content only; another doctor's content is 403
  * anonymous / plain user -> 404 (staff URLs are hidden, not merely denied)
  * orphaned content (owner Doctor deleted) -> superuser only, never a 500
  * `next=` on delete views must not redirect off-site
"""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image as PILImage

from apps.blog.models import BlogPost
from apps.core.models import Category
from apps.dashboard.models import Doctor
from apps.gallery.models import Gallery, Image
from apps.users.models import CustomUser


PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='x.jpg'):
    """Small valid JPEG — `validate_image` runs PIL's verify() on uploads."""
    buf = BytesIO()
    PILImage.new('RGB', (12, 12), (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class OwnershipMatrixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # `dashboard.signals` auto-creates the Doctor row when is_doctor=True.
        cls.doc_a_user = CustomUser.objects.create_user(
            username='doc_a', email='a@x.test', first_name='آ', last_name='الف',
            password=PASSWORD, is_doctor=True,
        )
        cls.doc_b_user = CustomUser.objects.create_user(
            username='doc_b', email='b@x.test', first_name='ب', last_name='بی',
            password=PASSWORD, is_doctor=True,
        )
        # Superuser that is NOT a doctor.
        cls.admin_user = CustomUser.objects.create_user(
            username='admin', email='admin@x.test', first_name='مدیر', last_name='کل',
            password=PASSWORD, is_superuser=True, is_staff=True,
        )
        # Superuser that IS ALSO a doctor — the case that used to be broken.
        cls.admin_doc_user = CustomUser.objects.create_user(
            username='admin_doc', email='ad@x.test', first_name='مدیر', last_name='پزشک',
            password=PASSWORD, is_doctor=True, is_superuser=True, is_staff=True,
        )
        # Plain authenticated user with no staff role at all.
        cls.plain_user = CustomUser.objects.create_user(
            username='plain', email='p@x.test', first_name='کاربر', last_name='ساده',
            password=PASSWORD,
        )

        cls.doc_a = Doctor.objects.get(user=cls.doc_a_user)
        cls.doc_b = Doctor.objects.get(user=cls.doc_b_user)
        cls.admin_doc = Doctor.objects.get(user=cls.admin_doc_user)

        cls.category = Category.objects.create(name='ایمپلنت')

        cls.post_a = BlogPost.objects.create(
            title='مقاله دکتر الف', slug='post-a', writer=cls.doc_a,
            content='محتوای آزمایشی برای مقاله دکتر الف که باید از پنجاه کاراکتر بیشتر باشد.',
            image=tiny_jpeg('post-a.jpg'),
        )
        cls.post_a.categories.set([cls.category])

        cls.gallery_a = Gallery.objects.create(doctor=cls.doc_a, category=cls.category)
        Image.objects.create(gallery=cls.gallery_a, image=tiny_jpeg('g-a.jpg'))

    def login(self, user):
        self.assertTrue(self.client.login(username=user.username, password=PASSWORD))

    # ------------------------------------------------------------ dashboard

    def test_superuser_reaches_any_dashboard(self):
        for actor in (self.admin_user, self.admin_doc_user):
            with self.subTest(actor=actor.username):
                self.login(actor)
                for doctor in (self.doc_a, self.doc_b):
                    resp = self.client.get(
                        reverse('dashboard:dashboard_doctor', args=[doctor.pk])
                    )
                    self.assertEqual(resp.status_code, 200)
                self.client.logout()

    def test_doctor_reaches_only_own_dashboard(self):
        self.login(self.doc_a_user)
        own = self.client.get(reverse('dashboard:dashboard_doctor', args=[self.doc_a.pk]))
        self.assertEqual(own.status_code, 200)

        other = self.client.get(reverse('dashboard:dashboard_doctor', args=[self.doc_b.pk]))
        self.assertEqual(other.status_code, 403)

    def test_dashboard_hidden_from_non_staff(self):
        url = reverse('dashboard:dashboard_doctor', args=[self.doc_a.pk])
        self.assertEqual(self.client.get(url).status_code, 404)  # anonymous

        self.login(self.plain_user)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_staff_urls_hidden_from_public(self):
        """
        Non-staff must get 404, never 403: a 403 confirms both the route and
        that the object id in the URL is real.
        """
        urls = [
            reverse('dashboard:dashboard_doctor', args=[self.doc_a.pk]),
            reverse('dashboard:dashboard_list'),
            reverse('blog:update_blog', args=[self.post_a.pk]),
            reverse('blog:delete_blog', args=[self.post_a.pk]),
            reverse('gallery:update_gallery', args=[self.gallery_a.pk]),
            reverse('gallery:delete_gallery', args=[self.gallery_a.pk]),
            reverse('gallery:clear_gallery_images', args=[self.gallery_a.pk]),
        ]
        for url in urls:
            with self.subTest(url=url, actor='anonymous'):
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url).status_code, 404)

        self.login(self.plain_user)
        for url in urls:
            with self.subTest(url=url, actor='plain'):
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url).status_code, 404)

    def test_dashboard_list_is_superuser_only(self):
        url = reverse('dashboard:dashboard_list')

        self.login(self.doc_a_user)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.logout()

        for actor in (self.admin_user, self.admin_doc_user):
            with self.subTest(actor=actor.username):
                self.login(actor)
                self.assertEqual(self.client.get(url).status_code, 200)
                self.client.logout()

    # ----------------------------------------------------------------- blog

    def test_superuser_can_edit_other_doctors_post(self):
        for actor in (self.admin_user, self.admin_doc_user):
            with self.subTest(actor=actor.username):
                self.login(actor)
                resp = self.client.get(reverse('blog:update_blog', args=[self.post_a.pk]))
                self.assertEqual(resp.status_code, 200)
                self.client.logout()

    def test_doctor_cannot_edit_other_doctors_post(self):
        self.login(self.doc_b_user)
        resp = self.client.get(reverse('blog:update_blog', args=[self.post_a.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_doctor_can_edit_own_post(self):
        self.login(self.doc_a_user)
        resp = self.client.get(reverse('blog:update_blog', args=[self.post_a.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_doctor_cannot_delete_other_doctors_post(self):
        self.login(self.doc_b_user)
        resp = self.client.post(reverse('blog:delete_blog', args=[self.post_a.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(BlogPost.objects.filter(pk=self.post_a.pk).exists())

    def test_superuser_can_delete_other_doctors_post(self):
        self.login(self.admin_doc_user)
        resp = self.client.post(reverse('blog:delete_blog', args=[self.post_a.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(BlogPost.objects.filter(pk=self.post_a.pk).exists())

    def test_orphaned_post_is_superuser_only_and_never_500s(self):
        """Deleting the owning Doctor leaves writer=None (SET_NULL)."""
        self.doc_a.delete()
        self.post_a.refresh_from_db()
        self.assertIsNone(self.post_a.writer)

        url = reverse('blog:update_blog', args=[self.post_a.pk])

        self.login(self.doc_b_user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()

        self.login(self.admin_user)
        self.assertEqual(self.client.get(url).status_code, 200)

    # -------------------------------------------------------------- gallery

    def test_superuser_can_edit_other_doctors_gallery(self):
        for actor in (self.admin_user, self.admin_doc_user):
            with self.subTest(actor=actor.username):
                self.login(actor)
                resp = self.client.get(
                    reverse('gallery:update_gallery', args=[self.gallery_a.pk])
                )
                self.assertEqual(resp.status_code, 200)
                self.client.logout()

    def test_doctor_cannot_edit_other_doctors_gallery(self):
        self.login(self.doc_b_user)
        resp = self.client.get(reverse('gallery:update_gallery', args=[self.gallery_a.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_doctor_can_edit_own_gallery(self):
        self.login(self.doc_a_user)
        resp = self.client.get(reverse('gallery:update_gallery', args=[self.gallery_a.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_doctor_cannot_mutate_other_doctors_gallery(self):
        """Every mutating gallery endpoint, not just the render view."""
        self.login(self.doc_b_user)
        pk = self.gallery_a.pk
        image = self.gallery_a.images.first()

        endpoints = [
            (reverse('gallery:update_gallery_category', args=[pk]), {'category': self.category.pk}),
            (reverse('gallery:add_gallery_images', args=[pk]), {}),
            (reverse('gallery:delete_gallery_image', args=[pk, image.pk]), {}),
            (reverse('gallery:clear_gallery_images', args=[pk]), {}),
            (reverse('gallery:delete_gallery', args=[pk]), {}),
        ]
        for url, payload in endpoints:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, payload).status_code, 403)

        self.assertTrue(Gallery.objects.filter(pk=pk).exists())
        self.assertEqual(self.gallery_a.images.count(), 1)

    def test_superuser_can_delete_other_doctors_gallery(self):
        self.login(self.admin_doc_user)
        resp = self.client.post(reverse('gallery:delete_gallery', args=[self.gallery_a.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Gallery.objects.filter(pk=self.gallery_a.pk).exists())

    def test_orphaned_gallery_is_superuser_only_and_never_500s(self):
        self.doc_a.delete()
        self.gallery_a.refresh_from_db()
        self.assertIsNone(self.gallery_a.doctor)

        url = reverse('gallery:update_gallery', args=[self.gallery_a.pk])

        self.login(self.doc_b_user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()

        self.login(self.admin_user)
        self.assertEqual(self.client.get(url).status_code, 200)

    # ------------------------------------------ rendered buttons match views

    def test_manage_buttons_shown_only_to_permitted_users(self):
        """
        The edit/delete controls a page renders must match what the views
        allow, otherwise staff either see dead buttons or miss real ones.
        """
        blog_edit = reverse('blog:update_blog', args=[self.post_a.pk])
        gal_edit = reverse('gallery:update_gallery', args=[self.gallery_a.pk])

        cases = [
            (self.admin_user, True, 'superuser (not doctor)'),
            (self.admin_doc_user, True, 'superuser + doctor'),
            (self.doc_a_user, True, 'owning doctor'),
            (self.doc_b_user, False, 'other doctor'),
        ]
        for actor, should_see, label in cases:
            self.login(actor)

            with self.subTest(page='blog list', actor=label):
                html = self.client.get(reverse('blog:blog_list')).content.decode()
                self.assertEqual(blog_edit in html, should_see)

            with self.subTest(page='blog detail', actor=label):
                html = self.client.get(
                    reverse('blog:blog_detail', args=[self.post_a.slug])
                ).content.decode()
                self.assertEqual(blog_edit in html, should_see)

            with self.subTest(page='gallery list', actor=label):
                html = self.client.get(reverse('gallery:gallery_list')).content.decode()
                self.assertEqual(gal_edit in html, should_see)

            self.client.logout()

    def test_public_never_sees_manage_buttons(self):
        blog_edit = reverse('blog:update_blog', args=[self.post_a.pk])
        gal_edit = reverse('gallery:update_gallery', args=[self.gallery_a.pk])

        for actor in (None, self.plain_user):
            if actor:
                self.login(actor)
            label = actor.username if actor else 'anonymous'

            with self.subTest(actor=label):
                blog_html = self.client.get(reverse('blog:blog_list')).content.decode()
                gal_html = self.client.get(reverse('gallery:gallery_list')).content.decode()
                self.assertNotIn(blog_edit, blog_html)
                self.assertNotIn(gal_edit, gal_html)
            self.client.logout()

    # ------------------------------------------------------- open redirect

    def test_delete_ignores_offsite_next(self):
        self.login(self.admin_user)

        resp = self.client.post(
            reverse('gallery:delete_gallery', args=[self.gallery_a.pk]),
            {'next': 'https://evil.example.com/phish'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('gallery:gallery_list'))

        resp = self.client.post(
            reverse('blog:delete_blog', args=[self.post_a.pk]),
            {'next': '//evil.example.com/phish'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('blog:blog_list'))

    def test_delete_honours_onsite_next(self):
        self.login(self.admin_user)
        target = reverse('dashboard:dashboard_doctor', args=[self.doc_a.pk])
        resp = self.client.post(
            reverse('blog:delete_blog', args=[self.post_a.pk]),
            {'next': target},
        )
        self.assertEqual(resp['Location'], target)


class OwnershipHelperTests(TestCase):
    """Unit-level checks for `utils.http.mixins.user_owns`."""

    @classmethod
    def setUpTestData(cls):
        cls.doc_user = CustomUser.objects.create_user(
            username='u_doc', email='ud@x.test', first_name='د', last_name='ک',
            password=PASSWORD, is_doctor=True,
        )
        cls.other_user = CustomUser.objects.create_user(
            username='u_other', email='uo@x.test', first_name='غ', last_name='ی',
            password=PASSWORD, is_doctor=True,
        )
        cls.super_user = CustomUser.objects.create_user(
            username='u_super', email='us@x.test', first_name='س', last_name='پ',
            password=PASSWORD, is_superuser=True,
        )
        cls.doc = Doctor.objects.get(user=cls.doc_user)

    def test_matrix(self):
        from django.contrib.auth.models import AnonymousUser

        from utils.http.mixins import user_owns

        cases = [
            (self.doc_user, self.doc, True, 'owner'),
            (self.other_user, self.doc, False, 'other doctor'),
            (self.super_user, self.doc, True, 'superuser'),
            (self.super_user, None, True, 'superuser + orphan'),
            (self.doc_user, None, False, 'doctor + orphan'),
            (AnonymousUser(), self.doc, False, 'anonymous'),
        ]
        for user, owner, expected, label in cases:
            with self.subTest(case=label):
                self.assertIs(user_owns(user, owner), expected)

    def test_get_doctor_profile_returns_none_without_row(self):
        from utils.http.mixins import get_doctor_profile

        self.assertEqual(get_doctor_profile(self.doc_user), self.doc)
        # Superuser with is_doctor=False has no profile row.
        self.assertIsNone(get_doctor_profile(self.super_user))
