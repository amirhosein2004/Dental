"""
Web Push: subscription bookkeeping and the guards around it.

Delivery itself is mocked — a real test would post to Google's push service.
What is worth pinning is everything around that call: who may register a
device, what an endpoint is allowed to be, and that a subscription the browser
has thrown away gets cleaned up instead of retried forever.
"""
import json
import re
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.dashboard.models import Doctor
from apps.notifications.models import PushSubscription
from apps.notifications.push import notify_staff, send_to_subscription
from apps.users.models import CustomUser

PASSWORD = 'test-pass-1234'
ENDPOINT = 'https://fcm.googleapis.com/fcm/send/abc123'


class PushSubscribeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='pushdoc', email='p@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )
        Doctor.objects.get(user=cls.staff)
        cls.other = CustomUser.objects.create_user(
            username='otherdoc', email='o@x.test', first_name='ر',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )

    def _post(self, url, payload):
        return self.client.post(
            url, data=json.dumps(payload), content_type='application/json',
        )

    def test_anonymous_cannot_subscribe(self):
        """404, not 403 — staff routes do not confirm they exist."""
        response = self._post(reverse('notifications:push_subscribe'), {
            'endpoint': ENDPOINT, 'p256dh': 'k', 'auth': 'a',
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_staff_subscribe_creates_a_row(self):
        self.client.login(username='pushdoc', password=PASSWORD)
        response = self._post(reverse('notifications:push_subscribe'), {
            'endpoint': ENDPOINT, 'p256dh': 'key', 'auth': 'auth',
        })

        self.assertEqual(response.status_code, 201)
        subscription = PushSubscription.objects.get()
        self.assertEqual(subscription.user, self.staff)
        self.assertEqual(subscription.endpoint, ENDPOINT)

    def test_resubscribing_the_same_browser_updates_rather_than_duplicates(self):
        """
        The endpoint is unique per browser. Two rows would deliver the same
        alert twice to one device.
        """
        self.client.login(username='pushdoc', password=PASSWORD)
        url = reverse('notifications:push_subscribe')
        self._post(url, {'endpoint': ENDPOINT, 'p256dh': 'k1', 'auth': 'a1'})
        response = self._post(url, {'endpoint': ENDPOINT, 'p256dh': 'k2', 'auth': 'a2'})

        self.assertEqual(response.status_code, 200)  # updated, not created
        self.assertEqual(PushSubscription.objects.count(), 1)
        self.assertEqual(PushSubscription.objects.get().p256dh, 'k2')

    def test_shared_browser_moves_to_whoever_signed_in_last(self):
        """A device belongs to one person at a time, not to both."""
        url = reverse('notifications:push_subscribe')
        self.client.login(username='pushdoc', password=PASSWORD)
        self._post(url, {'endpoint': ENDPOINT, 'p256dh': 'k', 'auth': 'a'})
        self.client.logout()
        self.client.login(username='otherdoc', password=PASSWORD)
        self._post(url, {'endpoint': ENDPOINT, 'p256dh': 'k', 'auth': 'a'})

        self.assertEqual(PushSubscription.objects.count(), 1)
        self.assertEqual(PushSubscription.objects.get().user, self.other)

    def test_incomplete_payload_is_rejected(self):
        self.client.login(username='pushdoc', password=PASSWORD)
        for payload in (
            {'endpoint': ENDPOINT, 'p256dh': 'k'},
            {'endpoint': ENDPOINT, 'auth': 'a'},
            {'p256dh': 'k', 'auth': 'a'},
        ):
            with self.subTest(payload=payload):
                response = self._post(reverse('notifications:push_subscribe'), payload)
                self.assertEqual(response.status_code, 400)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_non_https_endpoint_is_rejected(self):
        """
        The stored endpoint is a URL the server will later POST to on a trigger
        it does not control. Accepting an arbitrary one hands anyone with a
        staff account a request-forgery primitive.
        """
        self.client.login(username='pushdoc', password=PASSWORD)
        for bad in ('http://evil.test/x', 'file:///etc/passwd', 'http://127.0.0.1:8000/'):
            with self.subTest(endpoint=bad):
                response = self._post(reverse('notifications:push_subscribe'), {
                    'endpoint': bad, 'p256dh': 'k', 'auth': 'a',
                })
                self.assertEqual(response.status_code, 400)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_malformed_json_does_not_500(self):
        self.client.login(username='pushdoc', password=PASSWORD)
        response = self.client.post(
            reverse('notifications:push_subscribe'),
            data='not json at all', content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class PushUnsubscribeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='pushdoc', email='p@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )
        cls.other = CustomUser.objects.create_user(
            username='otherdoc', email='o@x.test', first_name='ر',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )

    def test_can_only_remove_own_device(self):
        theirs = PushSubscription.objects.create(
            user=self.other, endpoint=ENDPOINT, p256dh='k', auth='a',
        )
        self.client.login(username='pushdoc', password=PASSWORD)
        response = self.client.post(
            reverse('notifications:push_unsubscribe'),
            data=json.dumps({'endpoint': ENDPOINT}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['deleted'], 0)
        self.assertTrue(PushSubscription.objects.filter(pk=theirs.pk).exists())

    def test_removing_own_device_works(self):
        PushSubscription.objects.create(
            user=self.staff, endpoint=ENDPOINT, p256dh='k', auth='a',
        )
        self.client.login(username='pushdoc', password=PASSWORD)
        self.client.post(
            reverse('notifications:push_unsubscribe'),
            data=json.dumps({'endpoint': ENDPOINT}),
            content_type='application/json',
        )
        self.assertEqual(PushSubscription.objects.count(), 0)


# Push refuses to send without a VAPID keypair, and until these decorators
# existed these classes borrowed whatever was in the developer's own `.env` —
# so the suite passed on a machine that had keys and failed on one that did
# not, CI included. The values are syntactically valid and never leave the
# process: `webpush` itself is patched out in every test below.
WITH_VAPID = override_settings(
    VAPID_PUBLIC_KEY='BJxBQ4nJ2mYtRXHNGkVvPQzZ8kKvJ8oGqXHZ0kK5nJ2mYtRXHNGkVvPQzZ8kKvJ8oGqXHZ0kK5nJ2mYtRXHNGkQ',
    VAPID_PRIVATE_KEY='sXHNGkVvPQzZ8kKvJ8oGqXHZ0kK5nJ2mYtRXHNGkVvA',
    VAPID_SUBJECT='mailto:test@example.test',
)


@WITH_VAPID
class PushDeliveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='pushdoc', email='p@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )

    def _subscription(self, endpoint=ENDPOINT):
        return PushSubscription.objects.create(
            user=self.staff, endpoint=endpoint, p256dh='k', auth='a',
        )

    @patch('apps.notifications.push.webpush')
    def test_payload_carries_title_body_and_url(self, webpush):
        self._subscription()
        notify_staff('عنوان', 'متن', url='/contact/messages/', tag='t')

        payload = json.loads(webpush.call_args.kwargs['data'])
        self.assertEqual(payload['title'], 'عنوان')
        self.assertEqual(payload['body'], 'متن')
        self.assertEqual(payload['url'], '/contact/messages/')
        self.assertEqual(payload['tag'], 't')

    @patch('apps.notifications.push.webpush')
    def test_persian_text_is_not_escaped_into_ascii(self, webpush):
        """
        `ensure_ascii=True` would triple the payload; push services cap the
        body at 4KB, so a long Persian message would silently fail to send.
        """
        self._subscription()
        notify_staff('عنوان', 'متن فارسی')
        self.assertIn('متن فارسی', webpush.call_args.kwargs['data'])

    @patch('apps.notifications.push.webpush')
    def test_every_subscribed_device_gets_it(self, webpush):
        self._subscription('https://fcm.googleapis.com/a')
        self._subscription('https://updates.push.services.mozilla.com/b')

        sent, failed = notify_staff('عنوان', 'متن')
        self.assertEqual((sent, failed), (2, 0))
        self.assertEqual(webpush.call_count, 2)

    @patch('apps.notifications.push.webpush')
    def test_expired_subscription_is_deleted_not_retried(self, webpush):
        """
        410 Gone means the browser threw the subscription away. Keeping the row
        would push to a dead endpoint on every alert, forever.
        """
        from apps.notifications.push import WebPushException

        subscription = self._subscription()
        response = type('R', (), {'status_code': 410})()
        webpush.side_effect = WebPushException('gone', response=response)

        self.assertFalse(send_to_subscription(subscription, {'title': 'x'}))
        self.assertEqual(PushSubscription.objects.count(), 0)

    @patch('apps.notifications.push.webpush')
    def test_transient_failure_keeps_the_subscription(self, webpush):
        from apps.notifications.push import WebPushException

        subscription = self._subscription()
        response = type('R', (), {'status_code': 503})()
        webpush.side_effect = WebPushException('busy', response=response)

        self.assertFalse(send_to_subscription(subscription, {'title': 'x'}))
        self.assertEqual(PushSubscription.objects.count(), 1)

    @patch('apps.notifications.push.webpush')
    def test_delivery_failure_never_raises(self, webpush):
        """
        A push is queued from the contact-form view. An exception escaping here
        would turn a failed alert into a failed submit for the visitor.
        """
        self._subscription()
        webpush.side_effect = RuntimeError('boom')

        sent, failed = notify_staff('عنوان', 'متن')
        self.assertEqual((sent, failed), (0, 1))


class ContactMessagePushTests(TestCase):
    """The whole point: a visitor writing in wakes the clinic's devices."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='pushdoc', email='p@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )

    @patch('apps.contact.views.contact_view.push_staff_task.delay')
    @patch('apps.contact.views.contact_view.notify_staff_task.delay')
    def test_new_message_queues_a_push(self, _sms, push):
        from apps.contact.models import ContactMessage

        from apps.contact.views.contact_view import ContactView

        ContactView()._notify(ContactMessage(
            name='زهرا محمدی', phone='09121112233', message='سلام، مشاوره میخواستم',
        ))

        push.assert_called_once()
        args, kwargs = push.call_args
        self.assertIn('پیام جدید', args[0])
        self.assertIn('زهرا محمدی', args[1])
        self.assertEqual(kwargs['url'], '/contact/messages/')

    @patch('apps.contact.views.contact_view.notify_staff_task.delay')
    @patch('apps.contact.views.contact_view.push_staff_task.delay', side_effect=RuntimeError('broker down'))
    def test_a_dead_broker_does_not_break_the_alert_path(self, _push, _sms):
        """Both alerts are queued separately; neither may take the other down."""
        from apps.contact.models import ContactMessage
        from apps.contact.views.contact_view import ContactView

        # Must not raise.
        ContactView()._notify(ContactMessage(
            name='رضا', phone='09121112233', message='تست',
        ))


class PushToggleCsrfTests(TestCase):
    """
    The toggle has to be able to prove it is not a cross-site request.

    ``CSRF_COOKIE_HTTPONLY = True`` in production settings, and stage inherits
    it, so ``document.cookie`` cannot see ``csrftoken`` there at all. push.js
    read the token from the cookie and got an empty string, so every subscribe
    POST on the deployed site came back 403, no row was ever written, and every
    push after that reported "0 sent, 0 failed". Development leaves HTTPONLY
    off, which is exactly why the suite and local testing both stayed green.

    ``enforce_csrf_checks`` because the normal test client skips the check
    entirely — without it this test passes against the broken version too.
    """

    @classmethod
    def setUpTestData(cls):
        cls.staff = CustomUser.objects.create_user(
            username='csrfdoc', email='c@x.test', first_name='آ',
            last_name='ب', password=PASSWORD, is_doctor=True,
        )
        Doctor.objects.get(user=cls.staff)

    def _token_from_page(self, client):
        html = client.get(reverse('contact:messages')).content.decode()
        match = re.search(r'data-csrf="([^"]+)"', html)
        self.assertIsNotNone(match, 'the toggle renders no data-csrf attribute')
        return match.group(1)

    @override_settings(CSRF_COOKIE_HTTPONLY=True)
    def test_the_toggle_can_subscribe_with_the_cookie_hidden_from_js(self):
        client = Client(enforce_csrf_checks=True)
        client.login(username='csrfdoc', password=PASSWORD)

        response = client.post(
            reverse('notifications:push_subscribe'),
            data=json.dumps({'endpoint': ENDPOINT, 'p256dh': 'k', 'auth': 'a'}),
            content_type='application/json',
            headers={'x-csrftoken': self._token_from_page(client)},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(PushSubscription.objects.count(), 1)

    def test_the_script_does_not_rely_on_the_cookie_alone(self):
        """A cookie-only read is the bug; the attribute has to come first."""
        source = (Path(settings.BASE_DIR) / 'static' / 'js' / 'push.js').read_text(
            encoding='utf-8',
        )
        self.assertIn("getAttribute('data-csrf')", source)


class ServiceWorkerTests(TestCase):
    def test_served_from_the_site_root_with_the_right_headers(self):
        """
        Scope is capped by the serving directory: under /static/ the worker
        could only control /static/ and would never see a push for the site.
        """
        response = self.client.get('/sw.js')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')
        self.assertEqual(response['Service-Worker-Allowed'], '/')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn(b'addEventListener', response.content)


class WebAppManifestTests(TestCase):
    """
    The manifest is what makes the site installable, and on iOS installability
    is the precondition for push existing at all — Safari hides the Push API
    from a normal tab.
    """

    def setUp(self):
        self.response = self.client.get('/manifest.webmanifest')
        self.manifest = json.loads(self.response.content)

    def test_served_at_the_root_with_the_right_content_type(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response['Content-Type'], 'application/manifest+json')

    def test_scope_covers_the_whole_site(self):
        """
        A manifest scoped to /static/ would drop the installed app back into a
        browser tab on its first real navigation — and out of standalone mode
        is out of push on iOS.
        """
        self.assertEqual(self.manifest['scope'], '/')
        self.assertEqual(self.manifest['start_url'], '/')

    def test_display_is_standalone(self):
        """iOS grants Web Push only to a standalone web app."""
        self.assertEqual(self.manifest['display'], 'standalone')

    def test_has_the_icon_sizes_installers_require(self):
        sizes = {icon['sizes'] for icon in self.manifest['icons']}
        self.assertIn('192x192', sizes)
        self.assertIn('512x512', sizes)

    def test_has_a_maskable_icon(self):
        """Android launchers crop to a circle; without one the logo is shaved."""
        purposes = {icon.get('purpose') for icon in self.manifest['icons']}
        self.assertIn('maskable', purposes)

    def test_icon_files_actually_exist(self):
        """A manifest pointing at missing files fails install with no message."""
        from django.contrib.staticfiles import finders

        for icon in self.manifest['icons']:
            relative = icon['src'].replace('/static/', '', 1)
            with self.subTest(icon=relative):
                self.assertIsNotNone(
                    finders.find(relative), f'{relative} is missing',
                )

    def test_base_template_links_the_manifest_and_apple_icon(self):
        """
        Both are needed: the manifest for Android and current iOS, the Apple
        meta tags for older iOS. Having only one is the usual reason an
        installed icon opens in a plain browser view.
        """
        page = self.client.get('/contact/')
        html = page.content.decode()

        self.assertIn('rel="manifest"', html)
        self.assertIn('apple-touch-icon', html)
        self.assertIn('apple-mobile-web-app-capable', html)


class InstallableAppTests(TestCase):
    """
    What makes the site installable, as opposed to merely push-capable.

    The three pieces have to agree: a manifest at the root, a service worker
    registered for *every* visitor (not only staff who switched notifications
    on), and an offline page for the worker to fall back to.
    """

    def test_service_worker_is_registered_site_wide(self):
        """
        Chrome will not offer to install a site with no registered worker.
        Registration used to happen only inside the staff notification button,
        so an ordinary visitor never had one and the site was not installable.
        """
        html = self.client.get('/').content.decode()
        self.assertIn('js/pwa.js', html)

    def test_offline_page_renders(self):
        response = self.client.get('/offline/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'اتصال اینترنت برقرار نیست')

    def test_offline_page_is_not_indexed(self):
        """It is a fallback, not a page anyone should arrive at from search."""
        self.assertContains(self.client.get('/offline/'), 'noindex')

    def test_service_worker_precaches_only_the_offline_page(self):
        """
        The public pages already sit behind a 24-hour server-side response
        cache. A second HTML cache in the worker would make "why is this
        showing yesterday's content" close to undiagnosable, so the worker is
        allowed exactly one cached page.
        """
        body = self.client.get('/sw.js').content.decode()

        self.assertIn("OFFLINE_URL = '/offline/'", body)
        self.assertIn('cache.add', body)
        # One and only one thing is ever added to the cache.
        self.assertEqual(body.count('cache.add'), 1)

    def test_service_worker_only_intercepts_failed_navigations(self):
        """
        Passing everything else straight through is what keeps form posts, the
        AJAX "load more" endpoints and static assets behaving exactly as they
        would with no worker at all.
        """
        body = self.client.get('/sw.js').content.decode()

        self.assertIn("request.mode !== 'navigate'", body)
        self.assertIn("request.method !== 'GET'", body)

    def test_install_button_is_present_but_hidden_by_default(self):
        """
        Hidden in the markup and revealed by pwa.js for anyone not already
        running the installed app, so it never shows inside the app itself.
        """
        html = self.client.get('/').content.decode()
        self.assertIn('data-pwa-install', html)
        self.assertRegex(html, r'data-pwa-install[^>]*hidden')

    def test_staff_are_not_pitched_the_app(self):
        """
        The installed app is the patient's route back to booking. A doctor
        signed in already carries a bar full of their own controls, and on a
        phone this was one more pill competing with them.
        """
        doctor = CustomUser.objects.create_user(
            username='navdoc', email='n@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        # `force_login` would sign them in against the first backend in the
        # list, which is the throttle guard — its `get_user` returns None, so
        # the next request comes back anonymous and the assertion passes for
        # the wrong reason.
        self.client.login(username=doctor.username, password=PASSWORD)

        html = self.client.get('/').content.decode()

        self.assertNotIn('data-pwa-install', html)
        self.assertNotIn('pwaInstallDialog', html)

    def test_the_instructions_dialog_covers_both_platforms(self):
        """
        The fallback for every browser that hands us no install prompt:
        Safari never fires one, and Chrome stops after a dismissal.
        """
        html = self.client.get('/').content.decode()
        self.assertIn('pwaInstallDialog', html)
        self.assertIn('data-pwa-steps="ios"', html)
        self.assertIn('data-pwa-steps="other"', html)
        self.assertIn('Add to Home Screen', html)


@WITH_VAPID
class PushRecipientScopeTests(TestCase):
    """
    Who a staff alert actually reaches.

    The subscribe endpoint decides who may *register* a device. That decision
    is made once and the row outlives it, so the send path has to re-check —
    otherwise a former colleague's phone keeps receiving patients' names.
    """

    def setUp(self):
        self.doctor = CustomUser.objects.create_user(
            username='doc', email='d@x.test', first_name='آ', last_name='ب',
            password=PASSWORD, is_doctor=True,
        )
        self.admin = CustomUser.objects.create_user(
            username='boss', email='b@x.test', first_name='ر', last_name='ب',
            password=PASSWORD, is_superuser=True,
        )

    def _subscribe(self, user, endpoint):
        return PushSubscription.objects.create(
            user=user, endpoint=endpoint, p256dh='k', auth='a',
        )

    @patch('apps.notifications.push.webpush')
    def test_doctors_and_superusers_both_receive(self, webpush):
        self._subscribe(self.doctor, 'https://fcm.googleapis.com/doc')
        self._subscribe(self.admin, 'https://fcm.googleapis.com/boss')

        sent, _ = notify_staff('عنوان', 'متن')
        self.assertEqual(sent, 2)

    @patch('apps.notifications.push.webpush')
    def test_a_revoked_doctor_stops_receiving(self, webpush):
        """
        The flag is cleared when someone leaves. Their account is locked out of
        the site the same minute; the notifications must stop with it.
        """
        self._subscribe(self.doctor, 'https://fcm.googleapis.com/doc')
        self.doctor.is_doctor = False
        self.doctor.save()

        sent, failed = notify_staff('عنوان', 'متن')
        self.assertEqual((sent, failed), (0, 0))
        webpush.assert_not_called()

    @patch('apps.notifications.push.webpush')
    def test_a_deactivated_account_stops_receiving(self, webpush):
        self._subscribe(self.doctor, 'https://fcm.googleapis.com/doc')
        self.doctor.is_active = False
        self.doctor.save()

        sent, _ = notify_staff('عنوان', 'متن')
        self.assertEqual(sent, 0)
        webpush.assert_not_called()

    def test_a_patient_cannot_subscribe_at_all(self):
        """
        The endpoint is staff-gated, so a visitor never gets a row in the first
        place — the filter above is the second line, not the only one.
        """
        patient = CustomUser.objects.create_user(
            username='patient', email='pat@x.test', first_name='ز',
            last_name='م', password=PASSWORD,
        )
        self.client.force_login(patient)

        response = self.client.post(
            reverse('notifications:push_subscribe'),
            data=json.dumps({'endpoint': ENDPOINT, 'p256dh': 'k', 'auth': 'a'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(PushSubscription.objects.count(), 0)
