"""
The public contact form.

The only place on the site an anonymous visitor writes to the database, which
makes it the whole of the app's attack surface: captcha, honeypot, rate limit
and phone validation all live on this one POST. Each is tested for what it
lets through as much as for what it blocks — a spam guard that also rejects
real patients is its own kind of outage.
"""
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.contact.models import ContactMessage
from utils.security.math_captcha import SESSION_PREFIX


class ContactFormTests(TestCase):
    def setUp(self):
        # Both alerts are stubbed for every test here: the point is the form,
        # and a real Celery call would drag the broker into it.
        sms = patch('apps.contact.views.contact_view.notify_staff_task.delay')
        push = patch('apps.contact.views.contact_view.push_staff_task.delay')
        self.sms = sms.start()
        self.push = push.start()
        self.addCleanup(sms.stop)
        self.addCleanup(push.stop)

    def _solved_captcha(self):
        """
        Load the form and read the challenge back out of the session.

        The answer only exists server-side, so a test cannot "know" it any
        other way — and reaching into the session is exactly what a real
        visitor's eyes do with the rendered image.
        """
        self.client.get(reverse('contact:contact'))
        session = self.client.session
        key = [k for k in session.keys() if k.startswith(SESSION_PREFIX)][-1]
        return key[len(SESSION_PREFIX):], session[key]['answer']

    def _payload(self, **overrides):
        token, answer = self._solved_captcha()
        data = {
            'name': 'زهرا محمدی',
            'phone': '09121112233',
            'message': 'سلام، برای ایمپلنت میخواستم مشاوره بگیرم.',
            'captcha_token': token,
            'captcha': str(answer),
            'MyLoveDoctor': '',
        }
        data.update(overrides)
        return data

    # ---------------------------------------------------------- happy path --
    def test_a_valid_submission_is_stored(self):
        response = self.client.post(reverse('contact:contact'), self._payload())

        self.assertEqual(response.status_code, 302)
        message = ContactMessage.objects.get()
        self.assertEqual(message.name, 'زهرا محمدی')
        self.assertEqual(message.phone, '09121112233')
        self.assertFalse(message.is_read, 'a new message must arrive unread')

    def test_a_valid_submission_alerts_the_clinic(self):
        self.client.post(reverse('contact:contact'), self._payload())

        self.sms.assert_called_once()
        self.push.assert_called_once()

    def test_a_landline_number_is_accepted(self):
        """Not every patient has a mobile; 051… is a Mashhad landline."""
        self.client.post(reverse('contact:contact'), self._payload(phone='05147247247'))

        self.assertEqual(ContactMessage.objects.count(), 1)

    # ------------------------------------------------------------- captcha --
    def test_a_wrong_captcha_answer_is_rejected(self):
        token, answer = self._solved_captcha()
        response = self.client.post(reverse('contact:contact'), {
            'name': 'زهرا محمدی', 'phone': '09121112233', 'message': 'سلام، یک پیام آزمایشی است.',
            'captcha_token': token, 'captcha': str(answer + 1), 'MyLoveDoctor': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_a_missing_captcha_is_rejected(self):
        token, _answer = self._solved_captcha()
        response = self.client.post(reverse('contact:contact'), {
            'name': 'زهرا', 'phone': '09121112233', 'message': 'سلام، یک پیام آزمایشی است.',
            'captcha_token': token, 'MyLoveDoctor': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_a_challenge_cannot_be_answered_twice(self):
        """
        Replaying one solved challenge is how a script gets past a captcha
        cheaply: solve once by hand, then submit in a loop.
        """
        payload = self._payload()
        self.client.post(reverse('contact:contact'), payload)
        self.assertEqual(ContactMessage.objects.count(), 1)

        self.client.post(reverse('contact:contact'), payload)
        self.assertEqual(ContactMessage.objects.count(), 1, 'challenge was replayable')

    def test_an_invented_token_is_rejected(self):
        response = self.client.post(reverse('contact:contact'), {
            'name': 'زهرا', 'phone': '09121112233', 'message': 'سلام، یک پیام آزمایشی است.',
            'captcha_token': 'never-issued', 'captcha': '4', 'MyLoveDoctor': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    # ------------------------------------------------------------ honeypot --
    def test_a_filled_honeypot_is_rejected(self):
        """
        The field is hidden and unlabelled, so only something filling every
        input it finds will touch it.
        """
        response = self.client.post(
            reverse('contact:contact'), self._payload(MyLoveDoctor='spam'),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    # ---------------------------------------------------------- validation --
    def test_bad_phone_numbers_are_rejected(self):
        for phone in ('123', '0912111223', '091211122334', '+989121112233', 'abcdefghijk'):
            with self.subTest(phone=phone):
                response = self.client.post(
                    reverse('contact:contact'), self._payload(phone=phone),
                )
                self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_required_fields_are_enforced(self):
        for field in ('name', 'phone', 'message'):
            with self.subTest(missing=field):
                response = self.client.post(
                    reverse('contact:contact'), self._payload(**{field: ''}),
                )
                self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    # --------------------------------------------------------- rate limit ---
    @override_settings(RATELIMIT_ENABLE=True)
    def test_the_rate_limit_eventually_answers_429(self):
        """
        Disabled for the rest of the suite, so this is the one place the
        ceiling is exercised at all.
        """
        from django.core.cache import cache
        cache.clear()

        seen = set()
        for _ in range(30):
            seen.add(self.client.post(
                reverse('contact:contact'), self._payload(),
            ).status_code)
            if 429 in seen:
                break

        self.assertIn(429, seen, 'the form never refused a flood of submissions')

    # ------------------------------------------------------------- storage --
    def test_the_stored_message_is_not_html(self):
        """
        Staff read these in a page. Django escapes on output, so this only
        pins that nothing decided to be clever and pre-render them.
        """
        self.client.post(
            reverse('contact:contact'),
            self._payload(message='<script>alert(1)</script> سلام و درود بر شما'),
        )

        listing = self.client.get(reverse('contact:contact'))
        self.assertNotIn(b'<script>alert(1)</script>', listing.content)
