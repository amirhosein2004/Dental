"""
Web Push delivery.

Why this exists alongside the SMS path: an SMS costs money per message and
arrives whether or not anyone is at a screen. A push notification is free,
arrives in about a second, and lands on the device the staff member already
has in their hand — the right tool for "someone just wrote in", where the
value is speed rather than certainty of delivery.

No third-party service is involved. The browser hands us an endpoint at
Google's, Mozilla's or Apple's push service and its own encryption keys; we
sign each message with our VAPID key and the push service relays ciphertext it
cannot read. That matters here: the alert names a patient and quotes their
message.

Requirements, in the order they usually bite:

* **HTTPS.** Browsers only expose the Push API on a secure origin. `localhost`
  is exempt, so development works over plain HTTP.
* **A service worker at the site root.** A worker served from `/static/js/…`
  can only control `/static/…`; it has to be served from `/sw.js` to cover the
  whole site. `notifications.views.push_view.service_worker` does that.
* **iOS 16.4+, and only once the site is added to the home screen.** Safari
  refuses `pushManager.subscribe()` from a normal tab. Android Chrome and
  desktop browsers need no install.
"""
import json
import logging

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from .models import PushSubscription

logger = logging.getLogger(__name__)

try:
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover - exercised only on a broken install
    webpush = None
    WebPushException = Exception


def is_configured():
    """True when a VAPID keypair is present and the library is importable."""
    return bool(
        webpush is not None
        and getattr(settings, 'VAPID_PUBLIC_KEY', '')
        and getattr(settings, 'VAPID_PRIVATE_KEY', '')
    )


def _vapid_claims():
    """
    The `sub` claim tells the push service who to contact about abuse. It must
    be a mailto: or https: URL; push services reject the message without it.
    """
    return {'sub': settings.VAPID_SUBJECT}


def send_to_subscription(subscription, payload):
    """
    Deliver one notification.

    Returns True on success. A 404 or 410 from the push service means the
    browser threw the subscription away — the user cleared site data, or
    revoked permission — so the row is deleted rather than retried forever.
    Anything else is logged and reported as a failure without raising: an
    alert that cannot be delivered must not roll back the contact message that
    triggered it.
    """
    try:
        webpush(
            subscription_info=subscription.as_subscription_info(),
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims=_vapid_claims(),
            ttl=60 * 60 * 12,
        )
    except WebPushException as exc:
        status = getattr(getattr(exc, 'response', None), 'status_code', None)
        if status in (404, 410):
            logger.info('Push subscription gone (%s), removing: %s',
                        status, subscription.short_endpoint)
            subscription.delete()
        else:
            logger.warning('Push failed (%s) for %s: %s',
                           status, subscription.short_endpoint, exc)
        return False
    except Exception:
        logger.exception('Unexpected push failure for %s', subscription.short_endpoint)
        return False

    subscription.last_used_at = timezone.now()
    subscription.save(update_fields=['last_used_at'])
    return True


def notify_staff(title, body, url='/', tag=None):
    """
    Push to every browser a staff member has subscribed.

    Returns (sent, failed). Never raises — see `send_to_subscription`.

    `tag` collapses repeats: two messages arriving a minute apart replace each
    other in the tray instead of stacking, so a busy morning does not bury the
    phone in identical banners.
    """
    if not is_configured():
        logger.debug('Web push not configured; skipping "%s"', title)
        return 0, 0

    payload = {'title': title, 'body': body, 'url': url, 'tag': tag or 'clinic'}

    # Re-check staffness at send time, not only when the device subscribed.
    # `SubscribeView` gates who may register a browser, but that is a decision
    # made once; the row outlives it. A doctor who leaves the clinic has their
    # `is_doctor` flag cleared, and without this filter their phone would keep
    # receiving patients' names and numbers indefinitely — the account is
    # locked out of the site while the notifications carry on.
    recipients = (
        PushSubscription.objects
        .select_related('user')
        .filter(user__is_active=True)
        .filter(Q(user__is_doctor=True) | Q(user__is_superuser=True))
    )

    sent = failed = 0
    for subscription in recipients:
        if send_to_subscription(subscription, payload):
            sent += 1
        else:
            failed += 1

    logger.info('Push "%s": %s sent, %s failed', title, sent, failed)
    return sent, failed
