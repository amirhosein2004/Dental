from celery import shared_task

from .email_utils import send_otp_email


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
)
def send_otp_email_task(self, user_email, otp_code):
    """
    Send an OTP email asynchronously.

    Retries up to 3 times with exponential backoff (capped at 5 min) on any
    exception — SMTP outages, DNS blips, provider rate limits. Any error
    thrown by ``send_otp_email`` propagates and Celery reschedules the task.
    """
    return send_otp_email(user_email, otp_code)