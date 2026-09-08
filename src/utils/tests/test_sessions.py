"""
The signed OTP session token.

This is the gate between "correct password" and "correct one-time code". A
visitor holding a valid token is treated as a known user for the next two
minutes, so forging one would skip the password step entirely. The signature
and the expiry are the whole security of that, and neither had a test.
"""
from datetime import timedelta

from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from apps.users.models import CustomUser
from utils.security.sessions import SESSION_EXPIRY, generate_otp_token, validate_otp_token


def _request_with(token):
    """A request whose session carries `token`, or nothing when None."""
    request = RequestFactory().get('/')
    request.session = {} if token is None else {'otp_token': token}
    return request


class TokenRoundTripTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password='test-pass-1234', is_doctor=True,
        )

    def test_a_fresh_token_validates_back_to_its_user(self):
        user, error = validate_otp_token(_request_with(generate_otp_token(self.user)))

        self.assertIsNone(error)
        self.assertEqual(user, self.user)

    def test_two_tokens_for_one_user_differ(self):
        """
        The random half must actually be random. Identical tokens would mean a
        token captured once stays valid for every later login.
        """
        first = generate_otp_token(self.user)
        second = generate_otp_token(self.user)
        self.assertNotEqual(first, second)

    def test_missing_token_is_rejected(self):
        user, error = validate_otp_token(_request_with(None))

        self.assertIsNone(user)
        self.assertTrue(error)


class SignatureTests(TestCase):
    """
    The signature is the only thing stopping a visitor writing their own token.
    Every field is inside it, so tampering with any of them must fail.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password='test-pass-1234', is_doctor=True,
        )
        cls.victim = CustomUser.objects.create_user(
            username='boss', email='b@x.test', first_name='ر', last_name='ب',
            password='test-pass-1234', is_superuser=True,
        )

    def test_swapping_the_user_id_is_rejected(self):
        """
        The obvious attack: keep a valid signature, point it at someone else.
        Without the id inside the signed payload this would hand over any
        account whose id you can guess.
        """
        uid, rand, created, signature = generate_otp_token(self.user).split('|')
        forged = f'{self.victim.id}|{rand}|{created}|{signature}'

        user, error = validate_otp_token(_request_with(forged))
        self.assertIsNone(user)
        self.assertTrue(error)

    def test_a_tampered_signature_is_rejected(self):
        token = generate_otp_token(self.user)
        broken = token[:-1] + ('0' if token[-1] != '0' else '1')

        user, error = validate_otp_token(_request_with(broken))
        self.assertIsNone(user)
        self.assertTrue(error)

    def test_an_unsigned_token_is_rejected(self):
        """A token shaped right but signed with nothing at all."""
        forged = f'{self.user.id}|deadbeef|{timezone.now().isoformat()}|'

        user, error = validate_otp_token(_request_with(forged))
        self.assertIsNone(user)
        self.assertTrue(error)

    def test_moving_the_timestamp_forward_is_rejected(self):
        """Extending your own session by editing the date must not work."""
        uid, rand, _created, signature = generate_otp_token(self.user).split('|')
        future = (timezone.now() + timedelta(hours=2)).isoformat()

        user, error = validate_otp_token(_request_with(f'{uid}|{rand}|{future}|{signature}'))
        self.assertIsNone(user)
        self.assertTrue(error)

    @override_settings(OTP_SECRET_KEY='a-completely-different-key')
    def test_a_token_signed_with_another_key_is_rejected(self):
        """
        Rotating OTP_SECRET_KEY has to invalidate tokens already issued —
        that is the point of being able to rotate it.
        """
        # Signed under the original key by the fixture below.
        user, error = validate_otp_token(_request_with(self.stale_token))
        self.assertIsNone(user)
        self.assertTrue(error)

    def setUp(self):
        # Captured before any override_settings takes effect.
        self.stale_token = generate_otp_token(self.user)


class ExpiryTests(TestCase):
    """
    Kept equal to `OTP.is_valid()`'s window on purpose: a longer session token
    would let someone past this gate holding a code the next screen then
    rejects as expired.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password='test-pass-1234', is_doctor=True,
        )

    def _token_issued_at(self, moment):
        """A correctly signed token bearing an arbitrary issue time."""
        import hashlib
        import hmac

        from django.conf import settings

        payload = f'{self.user.id}|abc123|{moment.isoformat()}'
        signature = hmac.new(
            settings.OTP_SECRET_KEY.encode(), payload.encode(), hashlib.sha256,
        ).hexdigest()
        return f'{payload}|{signature}'

    def test_a_token_inside_the_window_is_accepted(self):
        moment = timezone.now() - (SESSION_EXPIRY / 2)

        user, error = validate_otp_token(_request_with(self._token_issued_at(moment)))
        self.assertIsNone(error)
        self.assertEqual(user, self.user)

    def test_a_token_past_the_window_is_rejected(self):
        moment = timezone.now() - SESSION_EXPIRY - timedelta(seconds=5)

        user, error = validate_otp_token(_request_with(self._token_issued_at(moment)))
        self.assertIsNone(user)
        self.assertTrue(error)

    def test_the_window_matches_the_otp_code_lifetime(self):
        """
        If these drift apart, one of the two screens starts rejecting people
        who did nothing wrong. Pinned so the drift is caught here rather than
        by a patient on the phone.
        """
        from apps.accounts.models import OTP

        otp = OTP(user=self.user)
        otp.generate_otp()

        otp.created_at = timezone.now() - SESSION_EXPIRY + timedelta(seconds=2)
        self.assertTrue(otp.is_valid(), 'code expired before the session token')

        otp.created_at = timezone.now() - SESSION_EXPIRY - timedelta(seconds=2)
        self.assertFalse(otp.is_valid(), 'code outlived the session token')


class MalformedTokenTests(TestCase):
    """
    Everything here arrives from a cookie the visitor controls. None of it may
    reach a 500 — an unhandled shape is an availability bug at best, and at
    worst a stack trace naming internals.
    """

    def test_junk_shapes_are_rejected_without_raising(self):
        for token in (
            '',                          # empty
            'not-a-token',               # no separators
            'a|b',                       # too few fields
            'a|b|c|d|e',                 # too many
            '1|r|not-a-date|sig',        # unparseable timestamp
            'notanint|r|2026-01-01T00:00:00|sig',
            '|||',
        ):
            with self.subTest(token=token):
                user, error = validate_otp_token(_request_with(token))
                self.assertIsNone(user)
                self.assertTrue(error)

    def test_a_token_for_a_deleted_user_is_rejected(self):
        """
        The account can be removed between issuing the token and using it. The
        lookup must fail closed rather than raising DoesNotExist.
        """
        user = CustomUser.objects.create_user(
            username='gone', email='g@x.test', first_name='آ', last_name='ب',
            password='test-pass-1234', is_doctor=True,
        )
        token = generate_otp_token(user)
        user.delete()

        resolved, error = validate_otp_token(_request_with(token))
        self.assertIsNone(resolved)
        self.assertTrue(error)
