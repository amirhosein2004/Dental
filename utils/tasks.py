from celery import shared_task
from .email_utils import send_otp_email

@shared_task
def send_otp_email_task(user_email, otp_code):
    """
    Sends an OTP email asynchronously using Celery.
    
    Args:
        user_email: The email address of the user.
        otp_code: The OTP code to send.
    
    Returns:
        bool: True if email was sent successfully, False otherwise.
    """
    return send_otp_email(user_email, otp_code)