from .common_imports import settings, get_user_model, timezone
from datetime import timedelta
import hmac
import hashlib
import secrets

User = get_user_model()

def generate_otp_token(user):
    """تولید توکن امضاشده برای سشن OTP"""
    secret_key = settings.OTP_SECRET_KEY
    random_token = secrets.token_hex(16)
    created_at = timezone.now().isoformat()  # زمان ساخت توکن
    token_data = f"{user.id}|{random_token}|{created_at}"
    token = hmac.new(
        secret_key.encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{user.id}|{random_token}|{created_at}|{token}"

def validate_otp_token(request):
    """اعتبارسنجی توکن OTP و برگردوندن کاربر"""
    otp_token = request.session.get('otp_token')
    if not otp_token:
        return None, "سشن نامعتبر است"

    try:
        user_id, random_token, created_at, token = otp_token.split('|')
        expected_token = hmac.new(
            settings.OTP_SECRET_KEY.encode(),
            f"{user_id}|{random_token}|{created_at}".encode(),
            hashlib.sha256
        ).hexdigest()

        if not secrets.compare_digest(token, expected_token):
            return None, "توکن دستکاری شده است"

        # چک کردن زمان انقضا
        created_time = timezone.datetime.fromisoformat(created_at)
        if timezone.now() > created_time + timedelta(minutes=5):
            return None, "جلسه شما منقضی شده است"

        return User.objects.get(id=user_id), None
    except (ValueError, User.DoesNotExist):
        return None, "کاربر یا توکن نامعتبر است"