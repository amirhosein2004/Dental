# prod.py (Production Settings)
from .base import *  # Import base settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),  # Database engine
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),  # Database name
        'USER': os.getenv('DB_USER', ''),  # Database user
        'PASSWORD': os.getenv('DB_PASSWORD', ''),  # Database password
        'HOST': os.getenv('DB_HOST', ''),  # Database host
        'PORT': os.getenv('DB_PORT', ''),  # Database port
        'CONN_MAX_AGE': 600,  # Maximum connection age
    }
}

# Security settings
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
X_FRAME_OPTIONS = "DENY"  # Prevent Clickjacking attacks (iFrame)
SESSION_COOKIE_SAMESITE = 'Strict'  # Prevent CSRF by restricting cross-site cookies

SECURE_SSL_REDIRECT = True  # Automatically redirect HTTP to HTTPS
SESSION_COOKIE_SECURE = True  # Send cookies only over HTTPS
CSRF_COOKIE_SECURE = True  # Enable CSRF only over HTTPS
SECURE_HSTS_SECONDS = 31536000  # Enable HSTS for 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply HSTS to all subdomains
SECURE_HSTS_PRELOAD = True  # Allow browsers to preload HSTS

# Sentry configuration for error tracking and performance monitoring
sentry_sdk.init(
    dsn=os.getenv('SENTRY_SDK_DSN', "https://d749550cb1e7cc53889ee73e51834163@o4509051631828992.ingest.us.sentry.io/4509051652800512"),  # Sentry DSN
    integrations=[DjangoIntegration()],  # Django integration
    traces_sample_rate=1.0,  # Performance monitoring sample rate
    send_default_pii=True  # Send user information (if required)
)