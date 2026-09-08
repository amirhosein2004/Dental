"""
Tests for the shared helpers in :mod:`utils`.

Each class here pins the behaviour of a security control that a plausible
refactor could quietly undo.
"""
import io

from PIL import Image

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase, override_settings

from utils.http.cache import get_cache_key
from utils.security.math_captcha import (
    IMAGE_HEIGHT,
    IMAGE_WIDTH,
    MAX_LIVE_CHALLENGES,
    SESSION_PREFIX,
    issue_challenge,
    render_challenge_image,
)
from utils.security.sanitize import sanitize_html
from utils.data.social import to_handle, to_url


class SanitizeHtmlTests(TestCase):
    """
    Blog bodies are rendered with ``|safe``, so anything that survives this
    function executes in every visitor's browser.
    """

    def test_script_tag_is_removed(self):
        cleaned = sanitize_html('<p>سلام</p><script>alert(1)</script>')
        self.assertNotIn('<script', cleaned)
        self.assertNotIn('alert(1)', cleaned)
        self.assertIn('سلام', cleaned)

    def test_event_handler_attribute_is_removed(self):
        cleaned = sanitize_html('<p onclick="steal()">متن</p>')
        self.assertNotIn('onclick', cleaned)
        self.assertIn('متن', cleaned)

    def test_javascript_url_is_removed(self):
        cleaned = sanitize_html('<a href="javascript:alert(1)">کلیک</a>')
        self.assertNotIn('javascript:', cleaned)

    def test_image_with_onerror_is_defused(self):
        cleaned = sanitize_html('<img src=x onerror="alert(1)">')
        self.assertNotIn('onerror', cleaned)

    def test_iframe_is_removed(self):
        self.assertNotIn('<iframe', sanitize_html('<iframe src="//evil"></iframe>'))

    def test_style_attribute_is_dropped(self):
        cleaned = sanitize_html('<p style="position:fixed;inset:0">x</p>')
        self.assertNotIn('style=', cleaned)

    def test_legitimate_editor_markup_survives(self):
        source = (
            '<h2>عنوان</h2><p><strong>پررنگ</strong> و <em>مورب</em></p>'
            '<ul><li>یک</li><li>دو</li></ul>'
            '<a href="https://example.com" title="t">لینک</a>'
            '<img src="https://example.com/a.jpg" alt="عکس">'
        )
        cleaned = sanitize_html(source)
        for fragment in ('<h2>', '<strong>', '<em>', '<ul>', '<li>',
                         'https://example.com', '<img'):
            self.assertIn(fragment, cleaned)

    def test_external_link_gets_noopener(self):
        cleaned = sanitize_html('<a href="https://example.com">x</a>')
        self.assertIn('noopener', cleaned)

    def test_empty_input_passes_through(self):
        self.assertEqual(sanitize_html(''), '')
        self.assertIsNone(sanitize_html(None))


class CacheKeyTests(TestCase):
    """
    The public list pages cache their whole response for a day. The key must
    depend only on parameters that change the response, or an attacker fills
    the cache with entries nobody will ever read.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, query=''):
        request = self.factory.get(f'/blog/{query}')
        request.user = AnonymousUser()
        return request

    def test_unknown_parameters_do_not_fork_the_key(self):
        base = get_cache_key(
            self._request(), cache_view='blogview', public=True,
            vary_on=('category',),
        )
        for junk in ('?x=1', '?x=2', '?utm_source=spam', '?a=1&b=2&c=3'):
            self.assertEqual(
                get_cache_key(
                    self._request(junk), cache_view='blogview', public=True,
                    vary_on=('category',),
                ),
                base,
                f'{junk} minted a separate cache entry',
            )

    def test_declared_parameters_do_fork_the_key(self):
        one = get_cache_key(
            self._request('?category=1'), cache_view='blogview', public=True,
            vary_on=('category',),
        )
        two = get_cache_key(
            self._request('?category=2'), cache_view='blogview', public=True,
            vary_on=('category',),
        )
        self.assertNotEqual(one, two)

    def test_parameter_order_does_not_matter(self):
        first = get_cache_key(
            self._request('?category=1&title=a'), cache_view='blogview',
            public=True, vary_on=('category', 'title'),
        )
        second = get_cache_key(
            self._request('?title=a&category=1'), cache_view='blogview',
            public=True, vary_on=('category', 'title'),
        )
        self.assertEqual(first, second)

    def test_multi_valued_filter_is_kept_whole(self):
        both = get_cache_key(
            self._request('?category=1&category=2'), cache_view='blogview',
            public=True, vary_on=('category',),
        )
        one = get_cache_key(
            self._request('?category=1'), cache_view='blogview',
            public=True, vary_on=('category',),
        )
        self.assertNotEqual(both, one)

    def test_view_without_vary_on_ignores_the_query_string_entirely(self):
        base = get_cache_key(self._request(), cache_view='home', public=True)
        noisy = get_cache_key(
            self._request('?anything=1'), cache_view='home', public=True,
        )
        self.assertEqual(base, noisy)

    def test_cache_view_is_required(self):
        with self.assertRaises(ValueError):
            get_cache_key(self._request(), cache_view='')


class CaptchaSessionGrowthTests(TestCase):
    """
    ``/math-captcha/refresh/`` is public and needs no login, and every call
    writes a challenge into the session. Without a bound, a loop against it
    grows one session record until the session store runs out of room.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get('/')
        request.session = self.client.session
        return request

    def _live(self, request):
        # `.keys()` explicitly: SessionBase has no __iter__, so a bare `for k
        # in session` falls back to __getitem__ with integer indices.
        return [k for k in request.session.keys() if k.startswith(SESSION_PREFIX)]

    def test_challenge_count_is_bounded(self):
        request = self._request()
        for _ in range(MAX_LIVE_CHALLENGES * 5):
            issue_challenge(request)
        self.assertLessEqual(len(self._live(request)), MAX_LIVE_CHALLENGES)

    def test_newest_challenge_always_survives_eviction(self):
        request = self._request()
        for _ in range(MAX_LIVE_CHALLENGES * 3):
            token = issue_challenge(request)
        self.assertIn(SESSION_PREFIX + token, request.session)

    @override_settings(RATELIMIT_ENABLE=False)
    def test_refresh_endpoint_returns_a_usable_token(self):
        response = self.client.post('/math-captcha/refresh/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('token', payload)
        self.assertEqual(
            self.client.get(payload['image_url']).status_code, 200,
        )

    def test_refresh_rejects_get(self):
        self.assertEqual(self.client.get('/math-captcha/refresh/').status_code, 405)


class SocialHandleTests(TestCase):
    """Doctors type a handle; the DB stores a usable URL."""

    def test_bare_handle_becomes_url(self):
        cases = [
            ('dr.babaei', 'instagram', 'https://instagram.com/dr.babaei'),
            ('sbdental', 'telegram', 'https://t.me/sbdental'),
            ('dr_behmadi', 'twitter', 'https://twitter.com/dr_behmadi'),
            ('dr-negar', 'linkedin', 'https://www.linkedin.com/in/dr-negar'),
        ]
        for handle, platform, expected in cases:
            with self.subTest(platform=platform):
                self.assertEqual(to_url(handle, platform), expected)

    def test_at_prefix_is_stripped(self):
        self.assertEqual(
            to_url('@dr.babaei', 'instagram'), 'https://instagram.com/dr.babaei'
        )

    def test_pasted_full_url_is_accepted(self):
        """People paste the address bar regardless of the label."""
        cases = [
            ('https://instagram.com/dr.babaei', 'instagram'),
            ('https://www.instagram.com/dr.babaei', 'instagram'),
            ('instagram.com/dr.babaei/', 'instagram'),
            ('http://instagram.com/dr.babaei', 'instagram'),
        ]
        for pasted, platform in cases:
            with self.subTest(pasted=pasted):
                self.assertEqual(
                    to_url(pasted, platform), 'https://instagram.com/dr.babaei'
                )

    def test_tracking_query_is_dropped(self):
        self.assertEqual(
            to_url('https://instagram.com/dr.babaei?igsh=abc123', 'instagram'),
            'https://instagram.com/dr.babaei',
        )

    def test_blank_stays_blank(self):
        for platform in ('instagram', 'telegram', 'twitter', 'linkedin'):
            with self.subTest(platform=platform):
                self.assertEqual(to_url('', platform), '')
                self.assertEqual(to_url('   ', platform), '')

    def test_invalid_handle_rejected(self):
        for bad in ('has spaces', 'emoji🦷', 'bad<script>', 'a,b'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    to_url(bad, 'instagram')

    def test_deep_path_falls_back_to_last_segment(self):
        """Deliberately lenient: a nested path yields its final segment."""
        self.assertEqual(to_url('a/b/c/dr.babaei', 'instagram'),
                         'https://instagram.com/dr.babaei')

    def test_round_trip_url_to_handle(self):
        cases = [
            ('https://instagram.com/dr.babaei', 'instagram', 'dr.babaei'),
            ('https://t.me/sbdental', 'telegram', 'sbdental'),
            ('https://www.linkedin.com/in/dr-negar', 'linkedin', 'dr-negar'),
            # Legacy/alternate host still yields the handle.
            ('https://x.com/dr_behmadi', 'twitter', 'dr_behmadi'),
            ('', 'instagram', ''),
        ]
        for url, platform, expected in cases:
            with self.subTest(url=url):
                self.assertEqual(to_handle(url, platform), expected)


class CaptchaRenderingTests(TestCase):
    """
    The captcha PNG actually comes out as a PNG.

    This path had no test, which mattered on the Pillow 11 -> 12 upgrade:
    every other captcha test asserts on session bookkeeping and would have
    stayed green while the image itself failed to draw. `ImageFont` and
    `ImageDraw.text` are the parts a Pillow major version can move.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get('/')
        request.session = self.client.session
        return request

    def _png(self):
        request = self._request()
        token = issue_challenge(request)
        result = render_challenge_image(request, token)
        # Whether the helper hands back a response or raw bytes, the bytes are
        # what a browser gets.
        return getattr(result, 'content', None) or result.getvalue()

    def test_it_returns_a_png_pillow_can_reopen(self):
        image = Image.open(io.BytesIO(self._png()))
        image.load()  # `open` is lazy; this is what forces the decode

        self.assertEqual(image.format, 'PNG')

    def test_the_image_has_the_configured_size(self):
        image = Image.open(io.BytesIO(self._png()))

        self.assertEqual(image.size, (IMAGE_WIDTH, IMAGE_HEIGHT))

    def test_the_digits_are_actually_drawn(self):
        """
        A blank canvas is a valid PNG of the right size, so size alone would
        not catch a font that silently drew nothing. Text and noise mean more
        than one colour.
        """
        image = Image.open(io.BytesIO(self._png())).convert('RGB')

        self.assertGreater(len(image.getcolors(maxcolors=100000) or []), 1)

    def test_an_unknown_token_does_not_render(self):
        with self.assertRaises(Http404):
            render_challenge_image(self._request(), 'not-a-real-token')
