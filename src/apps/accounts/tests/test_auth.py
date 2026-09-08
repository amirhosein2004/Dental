"""
Authentication surface.

These cover what an *unauthenticated* request is allowed to learn — the staff
routes answer 404 rather than 403 on purpose, so that a probe cannot use the
status code to map which accounts exist.
"""
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.users.models import CustomUser
from utils.security.login_throttle import (
    FAILURE_LIMIT,
    IP_FAILURE_LIMIT,
    clear,
    is_locked,
    record_failure,
)

PASSWORD = 'test-pass-1234'


class ChangePasswordAccessTests(TestCase):
    """
    ``ChangePasswordView.dispatch`` overrides the staff mixin, so it must call
    ``require_staff`` itself. Without that, the ownership check ran first and
    answered anonymous requests 403 for a real user id and 404 for a made-up
    one — turning the endpoint into a way to enumerate account ids.
    """

    @classmethod
    def setUpTestData(cls):
        cls.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='سعیده',
            last_name='بابایی', password=PASSWORD, is_doctor=True,
        )
        cls.other = CustomUser.objects.create_user(
            username='other', email='o@x.test', first_name='رضا',
            last_name='بهمدی', password=PASSWORD, is_doctor=True,
        )

    def _url(self, user_id):
        return reverse('accounts:change_password', kwargs={'user_id': user_id})

    def test_anonymous_gets_404_for_an_existing_user(self):
        self.assertEqual(self.client.get(self._url(self.doctor.pk)).status_code, 404)

    def test_anonymous_gets_404_for_a_missing_user(self):
        self.assertEqual(self.client.get(self._url(999999)).status_code, 404)

    def test_anonymous_cannot_distinguish_real_from_missing_ids(self):
        """The whole point: both answers must be identical."""
        real = self.client.get(self._url(self.doctor.pk))
        fake = self.client.get(self._url(999999))
        self.assertEqual(real.status_code, fake.status_code)

    def test_doctor_can_open_their_own_page(self):
        self.client.login(username='doc', password=PASSWORD)
        self.assertEqual(self.client.get(self._url(self.doctor.pk)).status_code, 200)

    def test_doctor_cannot_open_another_doctors_page(self):
        self.client.login(username='doc', password=PASSWORD)
        self.assertEqual(self.client.get(self._url(self.other.pk)).status_code, 403)


class LoginThrottleTests(TestCase):
    """
    Replaces django-axes. Counters live in the cache, so each test starts by
    clearing it — otherwise a lockout leaks into the next test.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='throttled', email='t@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )

    def setUp(self):
        cache.clear()

    def _request(self, ip='203.0.113.7'):
        request = RequestFactory().post('/auth/login/')
        request.META['REMOTE_ADDR'] = ip
        return request

    def test_correct_password_works_before_any_failures(self):
        request = self._request()
        self.assertIsNotNone(
            authenticate(request=request, username='throttled', password=PASSWORD)
        )

    def test_pair_is_refused_after_the_limit(self):
        request = self._request()
        for _ in range(FAILURE_LIMIT):
            record_failure(request, 'throttled')

        self.assertTrue(is_locked(request, 'throttled'))
        # Even the *correct* password must be refused — otherwise the limit
        # only slows a guesser down until they happen to get it right.
        self.assertIsNone(
            authenticate(request=request, username='throttled', password=PASSWORD)
        )

    def test_one_failure_short_of_the_limit_still_lets_you_in(self):
        request = self._request()
        for _ in range(FAILURE_LIMIT - 1):
            record_failure(request, 'throttled')

        self.assertFalse(is_locked(request, 'throttled'))
        self.assertIsNotNone(
            authenticate(request=request, username='throttled', password=PASSWORD)
        )

    def test_success_clears_the_counter(self):
        request = self._request()
        for _ in range(FAILURE_LIMIT - 1):
            record_failure(request, 'throttled')
        clear(request, 'throttled')

        for _ in range(FAILURE_LIMIT - 1):
            record_failure(request, 'throttled')
        self.assertFalse(is_locked(request, 'throttled'))

    def test_a_third_party_cannot_lock_someone_out_from_elsewhere(self):
        """
        Keyed on (ip, username), not username alone. Locking by username means
        anyone who knows a staff username can lock them out of their own
        account from anywhere — the protection becomes the attack.
        """
        attacker = self._request(ip='198.51.100.9')
        for _ in range(FAILURE_LIMIT * 2):
            record_failure(attacker, 'throttled')

        victim = self._request(ip='203.0.113.7')
        self.assertFalse(is_locked(victim, 'throttled'))
        self.assertIsNotNone(
            authenticate(request=victim, username='throttled', password=PASSWORD)
        )

    def test_username_spraying_from_one_ip_is_caught(self):
        """
        Walking through usernames keeps every pair under its own limit, so the
        per-IP counter is what stops it.
        """
        request = self._request(ip='198.51.100.10')
        for n in range(IP_FAILURE_LIMIT):
            record_failure(request, f'victim{n}')

        self.assertTrue(is_locked(request, 'someone-new'))

    def test_username_case_does_not_reset_the_counter(self):
        request = self._request()
        for _ in range(FAILURE_LIMIT):
            record_failure(request, 'throttled')

        self.assertTrue(is_locked(request, 'ThRoTtLeD'))

    def test_failed_login_through_the_form_is_counted(self):
        """End-to-end: the signal receiver must actually be connected."""
        for _ in range(FAILURE_LIMIT):
            self.client.post('/auth/login/', {
                'username': 'throttled', 'password': 'definitely-wrong',
            })

        request = RequestFactory().post('/auth/login/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        self.assertTrue(is_locked(request, 'throttled'))

    def test_authenticate_without_a_request_is_not_throttled(self):
        """A management command has no IP to key on; it must still work."""
        self.assertIsNotNone(
            authenticate(username='throttled', password=PASSWORD)
        )
