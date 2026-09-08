"""
SMS delivery back-ends.

The provider is chosen by ``settings.SMS_BACKEND`` so the panel can be swapped
(or switched off entirely in development) without touching call sites. Every
back-end takes an already-normalised list of numbers and returns a
:class:`SendResult`; none of them raise for per-number failures, because a bulk
run must not abort halfway because one number was rejected.
"""
import logging
from dataclasses import dataclass, field
from importlib import import_module

from django.conf import settings

logger = logging.getLogger(__name__)

# Kavenegar accepts at most 200 recipients per API call.
MAX_RECIPIENTS_PER_CALL = 200


@dataclass
class SendResult:
    sent: int = 0
    failed: int = 0
    error: str = ''
    provider_ids: list = field(default_factory=list)

    @property
    def ok(self):
        return self.failed == 0 and not self.error


class BaseSmsBackend:
    def send(self, numbers, message):  # pragma: no cover - interface
        raise NotImplementedError


class ConsoleSmsBackend(BaseSmsBackend):
    """
    Development back-end: logs instead of sending.

    Default on purpose — a misconfigured dev environment must never be able to
    spend real credit or text real patients.
    """

    def send(self, numbers, message):
        logger.info('[SMS:console] -> %s recipients\n%s', len(numbers), message)
        for number in numbers:
            logger.info('[SMS:console]   %s', number)
        return SendResult(sent=len(numbers))


class KavenegarSmsBackend(BaseSmsBackend):
    """
    Kavenegar REST back-end (``sms/send``: one text, many recipients).

    Requires ``KAVENEGAR_API_KEY``. ``KAVENEGAR_SENDER`` is optional — when
    omitted Kavenegar uses the account's default line.
    """

    endpoint = 'https://api.kavenegar.com/v1/{key}/sms/send.json'

    def __init__(self):
        self.api_key = getattr(settings, 'KAVENEGAR_API_KEY', '')
        self.sender = getattr(settings, 'KAVENEGAR_SENDER', '')
        if not self.api_key:
            raise ValueError('KAVENEGAR_API_KEY تنظیم نشده است')

    def send(self, numbers, message):
        # Imported lazily so the dependency is only needed when this back-end
        # is actually selected.
        import requests

        payload = {'receptor': ','.join(numbers), 'message': message}
        if self.sender:
            payload['sender'] = self.sender

        try:
            response = requests.post(
                self.endpoint.format(key=self.api_key), data=payload, timeout=20
            )
        except Exception as exc:  # network/DNS/timeout
            logger.exception('Kavenegar request failed')
            return SendResult(failed=len(numbers), error=str(exc))

        if response.status_code != 200:
            return SendResult(
                failed=len(numbers),
                error=f'HTTP {response.status_code}: {response.text[:200]}',
            )

        try:
            body = response.json()
        except ValueError:
            return SendResult(failed=len(numbers), error='پاسخ نامعتبر از سرویس پیامک')

        status = body.get('return', {}).get('status')
        if status != 200:
            return SendResult(
                failed=len(numbers),
                error=body.get('return', {}).get('message', f'status={status}'),
            )

        entries = body.get('entries') or []
        return SendResult(
            sent=len(entries) or len(numbers),
            provider_ids=[str(e.get('messageid')) for e in entries],
        )


_BACKENDS = {
    'console': ConsoleSmsBackend,
    'kavenegar': KavenegarSmsBackend,
}


def get_backend():
    """
    Resolve the configured back-end.

    Accepts a short name ('console', 'kavenegar') or a dotted import path so a
    custom panel can be plugged in without editing this module.
    """
    configured = getattr(settings, 'SMS_BACKEND', 'console')

    if configured in _BACKENDS:
        return _BACKENDS[configured]()

    module_path, _, class_name = configured.rpartition('.')
    if not module_path:
        raise ValueError(f'SMS_BACKEND نامعتبر است: {configured}')
    return getattr(import_module(module_path), class_name)()


def chunked(numbers, size=MAX_RECIPIENTS_PER_CALL):
    """Split recipients into provider-sized batches."""
    for start in range(0, len(numbers), size):
        yield numbers[start:start + size]
