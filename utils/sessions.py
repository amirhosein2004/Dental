from .common_imports import settings, get_user_model, timezone
from datetime import timedelta
import hmac
import hashlib
import secrets

User = get_user_model()

def generate_otp_token(user):
    """
    Generate a signed OTP token for the session.

    Args:
        user: The user object for whom the OTP token is being generated.

    Returns:
        A string representing the signed OTP token.
    """
    secret_key = settings.OTP_SECRET_KEY
    random_token = secrets.token_hex(16)  # Generate a random token
    created_at = timezone.now().isoformat()  # Token creation time
    token_data = f"{user.id}|{random_token}|{created_at}"
    
    # Create a HMAC SHA-256 signature of the token data
    token = hmac.new(
        secret_key.encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Return the complete token including the signature
    return f"{user.id}|{random_token}|{created_at}|{token}"

def validate_otp_token(request):
    """
    Validate the OTP token from the session and return the user.

    Args:
        request: The HTTP request object containing the session.

    Returns:
        A tuple containing the user object (or None if invalid) and an error message (or None if valid).
    """
    otp_token = request.session.get('otp_token')
    if not otp_token:
        return None, "سشن نامعتبر است"  # Invalid session

    try:
        # Split the token into its components
        user_id, random_token, created_at, token = otp_token.split('|')
        
        # Recreate the expected token using the same method as in generate_otp_token
        expected_token = hmac.new(
            settings.OTP_SECRET_KEY.encode(),
            f"{user_id}|{random_token}|{created_at}".encode(),
            hashlib.sha256
        ).hexdigest()

        # Compare the provided token with the expected token
        if not secrets.compare_digest(token, expected_token):
            return None, "توکن دستکاری شده است"  # Token has been tampered with

        # Check if the token has expired (valid for 5 minutes)
        created_time = timezone.datetime.fromisoformat(created_at)
        if timezone.now() > created_time + timedelta(minutes=5):
            return None, "جلسه شما منقضی شده است"  # Session has expired

        # Return the user object if everything is valid
        return User.objects.get(id=user_id), None
    except (ValueError, User.DoesNotExist):
        return None, "کاربر یا توکن نامعتبر است"  # Invalid user or token