"""
Async wrappers.

SMS panels are slow and occasionally unreachable; doing this inside the
request would make a patient wait on a third party to finish booking, and a
provider outage would surface as a failed booking. Everything goes through
Celery, mirroring the retry style of :mod:`utils.mail.tasks`.
"""
import logging

from celery import shared_task

from .models import NotificationLog
from .push import notify_staff as push_staff
from .services import notify_staff, send_sms

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def notify_staff_task(self, message, kind):
    """Fire an operational alert to the clinic's configured numbers."""
    log = notify_staff(message, kind)
    return log.pk


@shared_task(bind=True)
def send_bulk_sms_task(self, numbers, message, created_by_id=None):
    """
    Send a staff-composed message to a list of numbers.

    Deliberately **not** retried, unlike the alert task above.
    :func:`~notifications.services.send_sms` walks the list in batches of 200
    and already handles provider failure itself — it records the outcome and
    returns instead of raising. So the only way this task can raise is *after*
    some batches have gone out, and a retry would re-send every one of them:
    real messages, billed again, to patients who already got them. A partial
    send is visible in :class:`NotificationLog` and can be re-sent on purpose;
    a silent duplicate charge cannot be undone.
    """
    log = send_sms(
        numbers,
        message,
        kind=NotificationLog.Kind.BULK,
        created_by_id=created_by_id,
    )
    return log.pk


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 2},
)
def push_staff_task(self, title, body, url='/', tag=None):
    """
    Fire a browser notification to every subscribed staff device.

    Retried, unlike the bulk SMS task: a push costs nothing and is per-device
    idempotent from the recipient's point of view — the `tag` makes a repeat
    replace the banner already in the tray rather than adding a second one.
    Two attempts, because a push nobody sees within a minute has lost most of
    its value anyway.
    """
    sent, failed = push_staff(title, body, url=url, tag=tag)
    return {'sent': sent, 'failed': failed}
