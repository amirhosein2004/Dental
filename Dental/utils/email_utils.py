from .common_imports import send_mail, settings

def send_otp_email(user, otp_code):
    """
    Sends an email containing the OTP code to the user.

    Args:
        user: User object containing user details.
        otp_code: Generated OTP code.

    Returns:
        bool: True if the email was sent successfully, False otherwise.
    """
    subject = 'کد تأیید ورود پزشک'  # Email subject 
    message = f'کد ورود شما: {otp_code}\n\nاین کد فقط برای ۲ دقیقه معتبر است'  # Email message 
    from_email = settings.EMAIL_HOST_USER  # Sender's email address from settings
    recipient_list = [user.email]  # Recipient's email address

    try:
        # Attempt to send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=True,  # Prevents the program from crashing in case of an error
        )
        return True
    except Exception as e:
        return False