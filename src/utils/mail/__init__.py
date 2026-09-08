"""
Outbound email.

`email_utils` composes and sends; `tasks` is the Celery wrapper that retries
it, so a login is never held up by an SMTP timeout.
"""
