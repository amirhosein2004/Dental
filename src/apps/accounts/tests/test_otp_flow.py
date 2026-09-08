"""
The two-step login: password, then a one-time code by email.

The password alone is not enough to get in, and the code alone is not either —
so what matters here is that neither half can be skipped, and that a code is
single-use, short-lived, and belongs to exactly one account.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import OTP
from apps.users.models import CustomUser
from utils.security.math_captcha import SESSION_PREFIX
from utils.security.sessions import generate_otp_token
from apps.accounts.views.auth_view import _codes_match

PASSWORD = 'test-pass-1234'


class LoginStepTests(TestCase):
    """First step: correct credentials issue a code and nothing more."""

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        cls.patient = CustomUser.objects.create_user(
            username='patient', email='p@x.test', first_name='ز', last_name='م',
            password=PASSWORD,
        )

    def setUp(self):
        from django.core.cache import cache
        cache.clear()          # the login throttle counts in the cache
        patcher = patch('apps.accounts.views.auth_view.send_otp_email_task.delay')
        self.email = patcher.start()
        self.addCleanup(patcher.stop)

    def _solved_captcha(self):
        self.client.get(reverse('accounts:doctor_login'))
        session = self.client.session
        key = [k for k in session.keys() if k.startswith(SESSION_PREFIX)][-1]
        return key[len(SESSION_PREFIX):], session[key]['answer']

    def _login(self, username='doc', password=PASSWORD, **extra):
        token, answer = self._solved_captcha()
        data = {
            'username': username, 'password': password,
            'captcha_token': token, 'captcha': str(answer), 'MyLoveDoctor': '',
        }
        data.update(extra)
        return self.client.post(reverse('accounts:doctor_login'), data)

    def test_correct_credentials_send_a_code_and_do_not_log_in(self):
        response = self._login()

        self.assertRedirects(response, reverse('accounts:verify_otp'))
        self.email.assert_called_once()
        self.assertTrue(OTP.objects.filter(user=self.doctor).exists())
        # Crucially: not authenticated yet.
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_a_wrong_password_sends_no_code(self):
        response = self._login(password='wrong-pass-9999')

        self.assertEqual(response.status_code, 200)
        self.email.assert_not_called()
        self.assertFalse(OTP.objects.exists())

    def test_a_non_doctor_cannot_start_the_flow(self):
        """
        Correct credentials, wrong role. The check has to happen before a code
        is sent, or a patient account becomes a way to spam the mail queue.
        """
        response = self._login(username='patient')

        self.assertEqual(response.status_code, 200)
        self.email.assert_not_called()

    def test_a_filled_honeypot_sends_no_code(self):
        response = self._login(MyLoveDoctor='bot')

        self.assertEqual(response.status_code, 200)
        self.email.assert_not_called()

    def test_a_wrong_captcha_sends_no_code(self):
        token, answer = self._solved_captcha()
        response = self.client.post(reverse('accounts:doctor_login'), {
            'username': 'doc', 'password': PASSWORD,
            'captcha_token': token, 'captcha': str(answer + 1), 'MyLoveDoctor': '',
        })

        self.assertEqual(response.status_code, 200)
        self.email.assert_not_called()


class VerifyStepTests(TestCase):
    """Second step: the code. Reachable only with a valid session token."""

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.otp = OTP.objects.create(user=self.doctor)
        self.otp.generate_otp()

    def _hold_a_session_token(self, user=None):
        session = self.client.session
        session['otp_token'] = generate_otp_token(user or self.doctor)
        session.save()

    def _submit(self, code):
        self.client.get(reverse('accounts:verify_otp'))
        session = self.client.session
        key = [k for k in session.keys() if k.startswith(SESSION_PREFIX)][-1]
        return self.client.post(reverse('accounts:verify_otp'), {
            'otp': code,
            'captcha_token': key[len(SESSION_PREFIX):],
            'captcha': str(session[key]['answer']),
        })

    def test_the_page_is_unreachable_without_a_session_token(self):
        """
        Otherwise the first step could be skipped entirely: guess a code
        against a known account without ever proving the password.
        """
        response = self.client.get(reverse('accounts:verify_otp'))

        self.assertRedirects(response, reverse('accounts:doctor_login'))

    def test_the_correct_code_logs_the_user_in(self):
        self._hold_a_session_token()

        response = self._submit(self.otp.code)

        self.assertRedirects(response, reverse('home:home'))
        self.assertEqual(int(self.client.session['_auth_user_id']), self.doctor.pk)

    def test_the_code_is_consumed_on_use(self):
        """A code that survives its own use is a reusable password."""
        self._hold_a_session_token()
        self._submit(self.otp.code)

        self.assertFalse(OTP.objects.filter(pk=self.otp.pk).exists())

    def test_a_wrong_code_does_not_log_in(self):
        self._hold_a_session_token()
        wrong = '000000' if self.otp.code != '000000' else '111111'

        response = self._submit(wrong)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_a_wrong_code_does_not_consume_the_real_one(self):
        """Otherwise one wrong guess locks out the person who owns the code."""
        self._hold_a_session_token()
        self._submit('000000' if self.otp.code != '000000' else '111111')

        self.assertTrue(OTP.objects.filter(pk=self.otp.pk).exists())

    def test_an_expired_code_does_not_log_in(self):
        self._hold_a_session_token()
        OTP.objects.filter(pk=self.otp.pk).update(
            created_at=timezone.now() - timedelta(minutes=5),
        )

        response = self._submit(self.otp.code)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_another_users_code_does_not_work(self):
        """
        The code is looked up by the *session token's* user, so a code mailed
        to someone else must not open this session.
        """
        other = CustomUser.objects.create_user(
            username='other', email='o@x.test', first_name='ر', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        theirs = OTP.objects.create(user=other)
        theirs.generate_otp()

        self._hold_a_session_token()
        response = self._submit(theirs.code)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_the_session_is_cycled_on_login(self):
        """
        `session.flush()` before `login()` is what stops session fixation: a
        key handed to the visitor before they authenticated must not still be
        valid afterwards.
        """
        self._hold_a_session_token()
        before = self.client.session.session_key

        self._submit(self.otp.code)

        self.assertNotEqual(self.client.session.session_key, before)


class OtpCodeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )

    def test_a_code_is_six_digits(self):
        otp = OTP.objects.create(user=self.doctor)
        otp.generate_otp()

        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())

    def test_regenerating_replaces_the_previous_code(self):
        otp = OTP.objects.create(user=self.doctor)
        otp.generate_otp()
        first = otp.code

        otp.generate_otp()

        self.assertNotEqual(otp.code, first)
        self.assertEqual(OTP.objects.filter(user=self.doctor).count(), 1)

    def test_a_fresh_code_is_valid_and_an_old_one_is_not(self):
        otp = OTP.objects.create(user=self.doctor)
        otp.generate_otp()
        self.assertTrue(otp.is_valid())

        otp.created_at = timezone.now() - timedelta(minutes=3)
        self.assertFalse(otp.is_valid())


class CodeComparisonTests(TestCase):
    """
    The comparison helper behind OTP verification.

    It is `secrets.compare_digest` rather than `==` so a rejection takes the
    same time whatever the guess was; `==` returns at the first differing
    character, which turns a 6-digit search into a per-position one. The tests
    below pin the behaviour that a swap could quietly change — in particular
    that a null stored code is a mismatch rather than a 500, since the field
    is nullable and a row exists before its first `generate_otp()`.
    """

    def test_identical_codes_match(self):
        self.assertTrue(_codes_match('123456', '123456'))

    def test_different_codes_do_not_match(self):
        self.assertFalse(_codes_match('123456', '654321'))

    def test_a_shared_prefix_is_still_a_mismatch(self):
        """The case `==` would answer fastest, and the one being defended."""
        self.assertFalse(_codes_match('123456', '123450'))

    def test_a_missing_stored_code_is_a_mismatch_not_an_error(self):
        """`compare_digest` raises on None; the row exists before its first code."""
        self.assertFalse(_codes_match(None, '123456'))

    def test_an_empty_submission_is_a_mismatch(self):
        self.assertFalse(_codes_match('123456', ''))
