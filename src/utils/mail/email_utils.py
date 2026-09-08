from django.conf import settings
from django.core.mail import send_mail


def send_otp_email(user_email, otp_code):
    """
    Send an OTP code to the user's email.

    Args:
        user_email: Recipient email address.
        otp_code: Generated OTP code.

    Returns:
        bool: True if the email was sent (at least one recipient accepted).
    """
    subject = 'کد تأیید ورود پزشک'
    message = f'کد ورود شما: {otp_code}\n\nاین کد فقط برای ۲ دقیقه معتبر است'

    sent_count = send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user_email],
        fail_silently=False,
    )
    return sent_count > 0