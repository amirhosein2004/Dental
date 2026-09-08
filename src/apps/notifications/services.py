"""
The one place a message actually goes out.

Views and signals call these helpers; they never touch a provider directly.
Everything is written to :class:`NotificationLog` first so a crash mid-send
still leaves a trace.
"""
import logging

from django.conf import settings

from .models import NotificationLog
from .phones import parse_numbers
from .providers import chunked, get_backend

logger = logging.getLogger(__name__)


def staff_recipients():
    """
    Numbers that receive operational alerts (new message, new booking).

    Configured in settings rather than derived from user accounts: the person
    who should be interrupted at 9pm is a business decision, not whoever
    happens to have a doctor row.
    """
    raw = getattr(settings, 'STAFF_ALERT_NUMBERS', '') or ''
    numbers, _invalid = parse_numbers(raw)
    return numbers


def send_sms(numbers, message, kind, created_by_id=None):
    """
    Send `message` to `numbers`, batching to the provider's limit.

    Takes a user *id* rather than a user instance because this runs inside a
    Celery task and model instances are not JSON-serialisable.

    Always returns the :class:`NotificationLog` row. Never raises for delivery
    problems — a failed alert must not roll back the contact message or the
    booking that triggered it.
    """
    numbers = list(dict.fromkeys(n for n in numbers if n))

    log = NotificationLog.objects.create(
        kind=kind,
        message=message,
        recipient_count=len(numbers),
        recipients=','.join(numbers),
        created_by_id=created_by_id,
    )

    if not numbers:
        log.status = NotificationLog.Status.FAILED
        log.error = 'هیچ شماره‌ی معتبری برای ارسال وجود نداشت'
        log.save(update_fields=['status', 'error'])
        return log

    try:
        backend = get_backend()
    except Exception as exc:
        logger.exception('SMS backend unavailable')
        log.status = NotificationLog.Status.FAILED
        log.error = str(exc)
        log.save(update_fields=['status', 'error'])
        return log

    sent = failed = 0
    errors = []
    for batch in chunked(numbers):
        result = backend.send(batch, message)
        sent += result.sent
        failed += result.failed
        if result.error:
            errors.append(result.error)

    if failed == 0 and not errors:
        log.status = NotificationLog.Status.SENT
    elif sent == 0:
        log.status = NotificationLog.Status.FAILED
    else:
        log.status = NotificationLog.Status.PARTIAL

    log.sent_count = sent
    log.failed_count = failed
    log.error = ' | '.join(errors)[:2000]
    log.save(update_fields=['status', 'sent_count', 'failed_count', 'error'])
    return log


def notify_staff(message, kind):
    """Alert the clinic. No-ops (with a log row) when no numbers are configured."""
    return send_sms(staff_recipients(), message, kind)
