"""
The `ensure_superuser` command.

It exists because Django's `createsuperuser --noinput` sets an *unusable*
password: the account is created and cannot be signed into, which on a fresh
server looks like success until someone tries. The first test below is the one
that matters — the account must actually authenticate.
"""
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

User = get_user_model()

GOOD_PASSWORD = 'Kx7-clinic-9quiet'


class EnsureSuperuserTests(TestCase):
    def _run(self, **kwargs):
        options = {
            'username': 'admin', 'email': 'a@x.test',
            'password': GOOD_PASSWORD, 'verbosity': 0,
        }
        options.update(kwargs)
        call_command('ensure_superuser', **options)

    def test_the_created_account_can_actually_sign_in(self):
        """The whole reason this command exists rather than --noinput."""
        self._run()

        user = User.objects.get(username='admin')
        self.assertTrue(user.has_usable_password())
        self.assertIsNotNone(authenticate(username='admin', password=GOOD_PASSWORD))

    def test_it_creates_a_superuser_not_a_plain_user(self):
        self._run()

        user = User.objects.get(username='admin')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_running_twice_changes_nothing(self):
        """Safe to call from a deploy that runs on every release."""
        self._run()
        original = User.objects.get(username='admin').password

        self._run()

        self.assertEqual(User.objects.filter(username='admin').count(), 1)
        self.assertEqual(User.objects.get(username='admin').password, original)

    def test_update_password_resets_it(self):
        self._run()
        self._run(password='Different-9-pass', update_password=True)

        self.assertIsNotNone(
            authenticate(username='admin', password='Different-9-pass')
        )

    def test_an_existing_plain_user_is_promoted(self):
        """
        Being asked for a superuser when the row exists but is not one is how
        an account gets demoted by accident; the command repairs it.
        """
        User.objects.create_user(
            username='admin', email='a@x.test', first_name='آ', last_name='ب',
            password=GOOD_PASSWORD,
        )

        self._run()

        user = User.objects.get(username='admin')
        self.assertTrue(user.is_superuser)

    # ------------------------------------------------------------- refusals
    def test_a_weak_password_is_refused(self):
        for password in ('1234', 'password', '12345678'):
            with self.subTest(password=password):
                with self.assertRaises(CommandError):
                    self._run(password=password)
        self.assertFalse(User.objects.exists())

    def test_missing_values_are_named_not_guessed(self):
        with self.assertRaises(CommandError) as caught:
            call_command('ensure_superuser', username='admin', verbosity=0)

        message = str(caught.exception)
        self.assertIn('email', message)
        self.assertIn('password', message)

    def test_an_email_belonging_to_someone_else_is_refused(self):
        """
        The field is unique, so creating would fail anyway — with an
        IntegrityError that says less than this does.
        """
        User.objects.create_user(
            username='someone', email='taken@x.test', first_name='ر',
            last_name='ب', password=GOOD_PASSWORD,
        )

        with self.assertRaises(CommandError) as caught:
            self._run(email='taken@x.test')

        self.assertIn('someone', str(caught.exception))

    def test_validation_can_be_skipped_for_recovery(self):
        self._run(password='weak', skip_password_validation=True)

        self.assertTrue(User.objects.filter(username='admin').exists())
