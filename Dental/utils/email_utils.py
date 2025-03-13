from .common_imports import send_mail, settings


def send_otp_email(user, otp_code):
    """
    ارسال ایمیل حاوی کد OTP به کاربر

    Args:
        user: شیء کاربر
        otp_code: کد OTP تولید شده

    Returns:
        bool: موفقیت یا عدم موفقیت ارسال ایمیل
    """
    subject = 'کد تأیید ورود پزشک'
    message = f'کد ورود شما: {otp_code}\n\nاین کد فقط برای ۲ دقیقه معتبر است.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=True,  # جلوگیری از کرش کردن برنامه در صورت بروز خطا
        )
        return True
    except Exception as e:
        return False