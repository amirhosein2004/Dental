"""
Endpoints backing the browser push subscription flow.

Kept apart from `sms_view.py`, which is the staff SMS console: these are two
small JSON handlers plus the two files that have to be served from the site
root, and mixing them in would bury the SMS views they have nothing to do
with.
"""
import json
import logging

from django.contrib.staticfiles import finders
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_http_methods

from utils.http.mixins import DoctorOrSuperuserRequiredMixin, RateLimitMixin

from ..models import PushSubscription

logger = logging.getLogger(__name__)


def _payload(request):
    """Parse a JSON body, returning {} rather than raising on junk."""
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (ValueError, UnicodeDecodeError):
        return {}


class SubscribeView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """
    Record this browser's push subscription against the signed-in staff member.

    The endpoint URL is unique per browser, so `update_or_create` on it means
    re-subscribing the same device moves the row to whoever is signed in now
    rather than leaving a second row that would deliver the alert twice.
    """
    rate_limit = '20/m'

    def post(self, request, *args, **kwargs):
        data = _payload(request)
        endpoint = (data.get('endpoint') or '').strip()
        keys = data.get('keys') or {}
        p256dh = (data.get('p256dh') or keys.get('p256dh') or '').strip()
        auth = (data.get('auth') or keys.get('auth') or '').strip()

        if not (endpoint and p256dh and auth):
            return JsonResponse(
                {'error': 'اطلاعات اشتراک ناقص است'}, status=400,
            )

        # Only the push services we actually deliver through. Without this the
        # endpoint is an arbitrary URL the server will later POST to on a
        # trigger it does not control — a request-forgery primitive handed to
        # anyone with a staff account.
        if not endpoint.startswith('https://'):
            return JsonResponse({'error': 'آدرس مقصد معتبر نیست'}, status=400)

        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'p256dh': p256dh,
                'auth': auth,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:300],
            },
        )
        logger.info(
            'Push subscription %s for %s', 'created' if created else 'updated',
            request.user,
        )
        return JsonResponse({'ok': True, 'created': created}, status=201 if created else 200)


class UnsubscribeView(DoctorOrSuperuserRequiredMixin, RateLimitMixin, View):
    """
    Forget a subscription the browser has already dropped.

    Scoped to the caller's own rows: a staff member may turn off their own
    devices, not someone else's. Deleting nothing is still a success — the
    browser is unsubscribed either way, and reporting a failure would only
    make the button look broken.
    """
    rate_limit = '20/m'

    def post(self, request, *args, **kwargs):
        endpoint = (_payload(request).get('endpoint') or '').strip()
        if not endpoint:
            return JsonResponse({'error': 'آدرس مقصد لازم است'}, status=400)

        deleted, _ = PushSubscription.objects.filter(
            user=request.user, endpoint=endpoint,
        ).delete()
        return JsonResponse({'ok': True, 'deleted': deleted})


# HEAD as well as GET: uptime checks and some proxies probe with HEAD, and
# `require_GET` answers those with a 405 HTML page.
@require_http_methods(['GET', 'HEAD'])
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    """
    Serve the push service worker from the site root.

    A service worker can only control URLs under the path it was served from,
    so one delivered as `/static/js/push-sw.js` would have scope `/static/js/`
    and would never see a push meant for the site. Serving the same file at
    `/sw.js` gives it scope `/`.

    Never cached: a stale worker is the hardest kind of stale asset to clear,
    because it is the thing that would have to update itself.
    """
    # Resolve through the static machinery so the file is found whether it is
    # collected into STATIC_ROOT or still sitting in the project's static dir.
    path = finders.find('js/push-sw.js')
    if path is None:
        logger.error('push-sw.js not found by the staticfiles finders')
        return HttpResponse('// service worker missing', content_type='application/javascript')

    with open(path, 'rb') as handle:
        body = handle.read()

    response = HttpResponse(body, content_type='application/javascript')
    # Lets the worker claim the whole origin even though it is one file.
    response['Service-Worker-Allowed'] = '/'
    return response


@require_http_methods(['GET', 'HEAD'])
def web_app_manifest(request):
    """
    Serve the web app manifest from the site root.

    Root, not `/static/`, for the same reason as the service worker: a
    manifest's `scope` defaults to the directory it was served from, so one at
    `/static/site.webmanifest` would claim only `/static/` and the installed
    app would drop back into a normal browser tab the moment it navigated
    anywhere real. `scope` is set explicitly in the file as well; serving it
    from `/` means the two agree instead of relying on the override.

    Rendered as a template so the icon URLs come from `{% static %}` and keep
    working when the files are hashed or moved to the S3 bucket in production.
    """
    body = render_to_string('manifest.webmanifest', request=request)
    return HttpResponse(body, content_type='application/manifest+json')
