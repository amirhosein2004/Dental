# prod.py (Production Settings)
from .base import *  # Import base settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),  # Default to SQLite
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
        'CONN_MAX_AGE': 600,  # Persistent connections
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
    dsn=os.getenv('SENTRY_SDK_DSN'),  # Sentry DSN
    integrations=[DjangoIntegration()],  # Django integration
    traces_sample_rate=1.0,  # Performance monitoring sample rate
    send_default_pii=True  # Send user information (if required)
)

# Storage configuration for using S3-compatible storage
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage"  # Default storage backend
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"  # Static files storage backend
    }
}

# Liara bucket credentials and settings
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')  # Access key for Liara S3
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')  # Secret key for Liara S3
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')  # Name of the bucket in Liara
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')  # Endpoint URL for Liara S3
AWS_S3_FILE_OVERWRITE = False  # Prevent overwriting files with the same name