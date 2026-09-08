"""
The custom user model and its manager.

Two things matter here more than anything else on the model: that the
privilege flags cannot be set through anything a user touches, and that
`create_user` never leaves an account with a usable-but-unset password.
"""
import io

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from django.test import TestCase
from PIL import Image as PILImage

from apps.users.forms import CustomUserDoctorUpdateForm
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'


def tiny_jpeg(name='avatar.jpg', size=(10, 10)):
    buf = io.BytesIO()
    PILImage.new('RGB', size, (10, 120, 110)).save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), content_type='image/jpeg')


class ManagerTests(TestCase):
    def test_create_user_hashes_the_password(self):
        """
        A stored plaintext password would be readable by anyone with database
        access, and `check_password` would fail besides.
        """
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD,
        )

        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))

    def test_create_user_defaults_to_no_privileges(self):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD,
        )

        self.assertFalse(user.is_doctor)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_superuser_sets_both_flags(self):
        user = CustomUser.objects.create_superuser(
            username='boss', email='b@x.test', first_name='ر', last_name='ب',
            password=PASSWORD,
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_superuser_refuses_to_be_talked_out_of_the_flags(self):
        """
        Passing `is_superuser=False` to create_superuser is either a mistake or
        an attempt to mint a half-privileged account; either way it must fail
        loudly rather than produce something surprising.
        """
        for override in ({'is_staff': False}, {'is_superuser': False}):
            with self.subTest(override=override):
                with self.assertRaises(ValueError):
                    CustomUser.objects.create_superuser(
                        username='boss', email='b@x.test', first_name='ر',
                        last_name='ب', password=PASSWORD, **override,
                    )

    def test_username_and_email_are_required(self):
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                username='', email='d@x.test', first_name='آ', last_name='ب',
            )
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(
                username='doc', email='', first_name='آ', last_name='ب',
            )

    def test_the_email_domain_is_normalised(self):
        user = CustomUser.objects.create_user(
            username='doc', email='Doc@EXAMPLE.COM', first_name='آ',
            last_name='ب', password=PASSWORD,
        )

        self.assertEqual(user.email, 'Doc@example.com')


class UniquenessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD,
        )

    def test_a_duplicate_username_is_refused(self):
        with self.assertRaises((IntegrityError, ValidationError)):
            CustomUser.objects.create_user(
                username='doc', email='other@x.test', first_name='ر',
                last_name='ب', password=PASSWORD,
            )

    def test_a_duplicate_email_is_refused(self):
        with self.assertRaises((IntegrityError, ValidationError)):
            CustomUser.objects.create_user(
                username='other', email='d@x.test', first_name='ر',
                last_name='ب', password=PASSWORD,
            )


class ProfileFormTests(TestCase):
    """
    The one form a doctor uses on their own account. What it *omits* is the
    security property: `is_doctor`, `is_superuser` and `is_staff` are not
    fields, so no amount of extra POST data can raise a doctor to admin.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.other = CustomUser.objects.create_user(
            username='taken', email='taken@x.test', first_name='ر',
            last_name='ب', password=PASSWORD,
        )

    def test_privilege_flags_are_not_form_fields(self):
        form = CustomUserDoctorUpdateForm(instance=self.user)

        for flag in ('is_doctor', 'is_superuser', 'is_staff', 'is_active', 'password'):
            self.assertNotIn(flag, form.fields, f'{flag} is editable through the profile form')

    def test_posting_a_privilege_flag_has_no_effect(self):
        """The real check: extra POST keys must be ignored, not applied."""
        form = CustomUserDoctorUpdateForm(
            data={
                'username': 'doc', 'email': 'd@x.test',
                'first_name': 'آ', 'last_name': 'ب',
                'is_superuser': 'on', 'is_staff': 'on',
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()

        self.assertFalse(saved.is_superuser)
        self.assertFalse(saved.is_staff)

    def test_taking_another_account_username_is_refused(self):
        form = CustomUserDoctorUpdateForm(
            data={
                'username': 'taken', 'email': 'd@x.test',
                'first_name': 'آ', 'last_name': 'ب',
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_taking_another_account_email_is_refused(self):
        form = CustomUserDoctorUpdateForm(
            data={
                'username': 'doc', 'email': 'taken@x.test',
                'first_name': 'آ', 'last_name': 'ب',
            },
            instance=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_keeping_your_own_username_is_allowed(self):
        """
        The uniqueness check excludes the row being edited. Without that, a
        doctor could never save any change without also renaming themselves.
        """
        form = CustomUserDoctorUpdateForm(
            data={
                'username': 'doc', 'email': 'd@x.test',
                'first_name': 'آی', 'last_name': 'ب',
            },
            instance=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)


class ProfileImageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD,
        )

    def test_a_valid_jpeg_is_accepted(self):
        self.user.image = tiny_jpeg()
        self.user.full_clean()          # must not raise

    def test_a_file_that_is_not_an_image_is_rejected(self):
        """
        Extension alone is not enough: this is a text file wearing `.jpg`.
        `validate_image` opens it, which is what catches it.
        """
        self.user.image = SimpleUploadedFile(
            'evil.jpg', b'<?php echo "not an image"; ?>', content_type='image/jpeg',
        )

        with self.assertRaises(ValidationError):
            self.user.full_clean()

    def test_a_disallowed_extension_is_rejected(self):
        self.user.image = SimpleUploadedFile(
            'shell.svg', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>',
            content_type='image/svg+xml',
        )

        with self.assertRaises(ValidationError):
            self.user.full_clean()


class UserStringTests(TestCase):
    def test_full_name_joins_both_parts(self):
        user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD,
        )

        self.assertEqual(user.get_full_name, 'سعیده بابایی')
        self.assertEqual(str(user), 'doc')

    def test_permissions_follow_superuser_only(self):
        """
        `has_perm` is overridden to ignore Django's permission tables entirely
        — the site has exactly two roles. Pinned so a future reader does not
        assume group permissions work.
        """
        doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        admin = CustomUser.objects.create_superuser(
            username='boss', email='b@x.test', first_name='ر', last_name='ب',
            password=PASSWORD,
        )

        self.assertFalse(doctor.has_perm('anything'))
        self.assertTrue(admin.has_perm('anything'))
        self.assertFalse(doctor.has_module_perms('blog'))
        self.assertTrue(admin.has_module_perms('blog'))
