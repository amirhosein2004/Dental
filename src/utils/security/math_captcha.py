"""
Session-backed math captcha.

Reason for existence: replaces the paid Google reCAPTCHA integration. Zero DB
tables added; the challenge answer lives only in ``request.session`` under a
unique token and is consumed on validation.

Usage:
    class MyForm(MathCaptchaFormMixin, forms.Form):
        ...

    # In the view (both GET and POST):
    form = MyForm(request.POST or None, request=request)

The mixin adds two fields to the form:
    ``captcha_token``  — HiddenInput carrying the session key
    ``captcha``        — the user-facing answer input. Its widget renders an
                         inline noisy PNG of the challenge before the input,
                         plus a refresh button, so a plain ``{{ form.captcha }}``
                         in the template is enough.
"""

from __future__ import annotations

import io
import json
import random
import secrets

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from django import forms
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from utils.http.mixins import client_ip_rate_key


SESSION_PREFIX = 'mathcap:'
OPERATORS = ('+', '-')
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 55

# How many unconsumed challenges one session may hold. Every issue_challenge
# call wrote a new session key and nothing ever removed the old ones, while
# `/math-captcha/refresh/` is public and needs no login — so a loop against it
# grew one session record without limit, in the same Redis the site caches
# into. A form needs exactly one live challenge; a handful of spares covers
# two tabs and a few refreshes.
MAX_LIVE_CHALLENGES = 8

# Ceiling on refreshes per IP. The button is meant to be pressed when the
# image is unreadable, not thousands of times a minute.
REFRESH_RATE = '30/m'


def _new_challenge():
    """Generate a small non-negative arithmetic problem."""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    op = random.choice(OPERATORS)
    if op == '-' and b > a:
        a, b = b, a
    expr = f"{a} {op} {b}"
    answer = a + b if op == '+' else a - b
    return expr, answer


def _evict_oldest(session):
    """
    Drop the least recently issued challenges until the session is back under
    :data:`MAX_LIVE_CHALLENGES`.

    Insertion order is enough to identify the oldest: Python dicts — and the
    session dict — preserve it, and challenges are only ever appended.
    """
    keys = [k for k in session.keys() if k.startswith(SESSION_PREFIX)]
    excess = len(keys) - MAX_LIVE_CHALLENGES
    for key in keys[:excess] if excess > 0 else []:
        session.pop(key, None)


def issue_challenge(request) -> str:
    """Create a new challenge, store its answer in session, return the token."""
    token = secrets.token_urlsafe(12)
    expr, answer = _new_challenge()
    request.session[SESSION_PREFIX + token] = {'expr': expr, 'answer': answer}
    # Bound the session before it is written back, not after.
    _evict_oldest(request.session)
    request.session.modified = True
    return token


def peek_challenge(request, token):
    return request.session.get(SESSION_PREFIX + token)


def pop_challenge(request, token):
    """Consume the challenge. Returns the expected answer or ``None``."""
    data = request.session.pop(SESSION_PREFIX + token, None)
    if data is None:
        return None
    request.session.modified = True
    return data['answer']


def render_challenge_image(request, token):
    """View: render the challenge as a noisy PNG. 404 if the token is stale."""
    data = peek_challenge(request, token)
    if data is None:
        raise Http404('challenge expired')
    return _make_image_response(data['expr'])


@require_POST
@ratelimit(key=client_ip_rate_key, rate=REFRESH_RATE, method='POST', block=True)
def refresh_challenge(request):
    """
    View: issue a fresh challenge for the current session and return the new
    token + image URL as JSON. The client swaps its hidden input and <img>.

    Rate-limited and bounded: this endpoint is public and needs no login, and
    each call writes to the session store. :func:`issue_challenge` evicts the
    oldest entries so one session cannot grow without limit.
    """
    token = issue_challenge(request)
    return JsonResponse({
        'token': token,
        'image_url': reverse('math_captcha_image', kwargs={'token': token}),
    })


def _make_image_response(text: str) -> HttpResponse:
    img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # Point noise
    for _ in range(300):
        x = random.randint(0, IMAGE_WIDTH - 1)
        y = random.randint(0, IMAGE_HEIGHT - 1)
        shade = random.randint(80, 200)
        draw.point((x, y), fill=(shade, shade, shade))

    # A couple of curved-ish lines
    for _ in range(3):
        draw.line(
            [
                (random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)),
                (random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT)),
            ],
            fill=(random.randint(100, 200),) * 3,
            width=1,
        )

    try:
        font = ImageFont.load_default(size=26)
    except TypeError:
        # Older Pillow: fixed-size default.
        font = ImageFont.load_default()

    draw.text((15, 12), f"{text} = ?", fill=(30, 30, 30), font=font)
    img = img.filter(ImageFilter.SMOOTH)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response['Pragma'] = 'no-cache'
    return response


class _CaptchaTokenWidget(forms.HiddenInput):
    """
    HiddenInput that always renders the current ``captcha_token`` attribute,
    ignoring whatever value POST data supplies. This is essential when the
    mixin rotates the token after a failed attempt: without this, the hidden
    input would keep re-submitting the stale (already-consumed) token.
    """

    captcha_token: str | None = None

    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, self.captcha_token or value, attrs, renderer)


class MathCaptchaAnswerWidget(forms.NumberInput):
    """NumberInput that prepends the challenge image + refresh button."""

    captcha_token: str | None = None

    def render(self, name, value, attrs=None, renderer=None):
        input_html = super().render(name, value, attrs, renderer)
        if not self.captcha_token:
            return input_html
        img_url = reverse('math_captcha_image', kwargs={'token': self.captcha_token})
        refresh_url = reverse('math_captcha_refresh')
        # ``data-*`` attrs let the small runtime in auth.js wire the refresh
        # button to swap the image + hidden token without a page reload.
        markup = (
            '<div class="math-captcha" '
            f'data-refresh-url="{refresh_url}" '
            f'data-image-base="{reverse("math_captcha_image", kwargs={"token": "__TOKEN__"})}">'
            '  <div class="math-captcha__image-wrap">'
            f'    <img src="{img_url}" alt="کد امنیتی" class="math-captcha__image" '
            f'         width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}" data-captcha-image>'
            '    <button type="button" class="math-captcha__refresh" '
            '            data-captcha-refresh aria-label="بارگذاری کد امنیتی جدید" '
            '            title="کد جدید">'
            '      <i class="fas fa-rotate"></i>'
            '    </button>'
            '  </div>'
            f'  {input_html}'
            '</div>'
        )
        return mark_safe(markup)


class MathCaptchaFormMixin:
    """
    Add a session-backed math captcha to a Form. The view MUST pass
    ``request=request`` when instantiating the form.
    """

    _CAPTCHA_ERROR = 'کد امنیتی نادرست است، لطفا دوباره تلاش کنید'

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._captcha_request = request

        self.fields['captcha_token'] = forms.CharField(
            widget=_CaptchaTokenWidget(),
            required=True,
        )
        self.fields['captcha'] = forms.IntegerField(
            label='کد امنیتی',
            widget=MathCaptchaAnswerWidget(attrs={
                'class': 'math-captcha__input',
                'placeholder': 'حاصل عبارت را وارد کنید',
                'autocomplete': 'off',
                'inputmode': 'numeric',
            }),
            error_messages={
                'required': 'لطفاً حاصل عبارت را وارد کنید',
                'invalid': 'یک عدد صحیح وارد کنید',
            },
        )

        self._set_token(self._resolve_token())

    def _set_token(self, token: str | None):
        """Bind ``token`` to both widgets so re-render always uses the latest."""
        self.fields['captcha_token'].initial = token
        self.fields['captcha_token'].widget.captcha_token = token
        self.fields['captcha'].widget.captcha_token = token

    def _resolve_token(self) -> str | None:
        """
        Pick the token to bind to the widget:
          - GET: fresh token
          - POST: keep the submitted token if it still exists in session,
            otherwise issue a new one (previous attempt consumed it).
        """
        if self._captcha_request is None:
            return None
        if self.is_bound:
            token = self.data.get('captcha_token')
            if token and peek_challenge(self._captcha_request, token) is not None:
                return token
        return issue_challenge(self._captcha_request)

    def clean(self):
        cleaned = super().clean()
        token = cleaned.get('captcha_token')
        answer = cleaned.get('captcha')

        if self._captcha_request is None:
            # Server misconfiguration: reject rather than silently pass.
            raise ValidationError(self._CAPTCHA_ERROR)

        if token is None or answer is None:
            # Empty submit or non-integer answer. Retire whatever token the
            # form did carry (avoid leaving orphaned challenges in the
            # session) and hand the user a fresh one for the next render.
            if token:
                pop_challenge(self._captcha_request, token)
            self._set_token(issue_challenge(self._captcha_request))
            return cleaned

        # Peek — don't consume yet. We only pop the challenge once we know
        # whether the form as a whole is valid; otherwise a re-render caused by
        # an unrelated field error would leave the image endpoint 404-ing.
        challenge = peek_challenge(self._captcha_request, token)
        if challenge is None:
            self._set_token(issue_challenge(self._captcha_request))
            self.add_error('captcha', self._CAPTCHA_ERROR)
            return cleaned

        if int(answer) != int(challenge['answer']):
            pop_challenge(self._captcha_request, token)
            self._set_token(issue_challenge(self._captcha_request))
            self.add_error('captcha', self._CAPTCHA_ERROR)
            return cleaned

        # Captcha correct. `self.errors` at this point already contains any
        # per-field errors that fired before `clean()`. If the form is otherwise
        # valid we consume the challenge; if not, we retire the old one and
        # issue a fresh challenge so the re-rendered widget has a live image.
        pop_challenge(self._captcha_request, token)
        if self.errors:
            self._set_token(issue_challenge(self._captcha_request))
        return cleaned
