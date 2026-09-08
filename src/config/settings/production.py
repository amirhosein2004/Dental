# prod.py (Production Settings)
from .base import *  # Import base settings

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

# TLS terminates at nginx, which then talks plain HTTP to gunicorn. Without
# this, `request.is_secure()` is always False behind the proxy, so
# SECURE_SSL_REDIRECT below would redirect an already-HTTPS request back to
# HTTPS — forever. The header is only trustworthy because nginx sets it on
# every proxied request, overwriting anything the client sent.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_SSL_REDIRECT = True  # Automatically redirect HTTP to HTTPS
SESSION_COOKIE_SECURE = True  # Send cookies only over HTTPS
CSRF_COOKIE_SECURE = True  # Enable CSRF only over HTTPS
SECURE_HSTS_SECONDS = 31536000  # Enable HSTS for 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Apply HSTS to all subdomains
SECURE_HSTS_PRELOAD = True  # Allow browsers to preload HSTS

# Liara bucket credentials and settings
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')  # Access key for Liara S3
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')  # Secret key for Liara S3
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')  # Name of the bucket in Liara
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')  # Endpoint URL for Liara S3
AWS_S3_FILE_OVERWRITE = False  # Prevent overwriting files with the same name
AWS_QUERYSTRING_AUTH = False  # Disable query string authentication for S3 URLs

# Uploads go to the bucket when there is a bucket, and to local disk when
# there is not.
#
# The backend used to be S3 unconditionally. On Liara that is right — the
# filesystem there is ephemeral, so anything written to it is gone at the next
# deploy. On a plain VPS it is not: there is no bucket, and every upload died
# with `EndpointConnectionError: Could not connect to the endpoint URL`, from
# a setting no environment file could change. nginx has served /media/ from
# disk all along, waiting for exactly this.
#
# The credentials decide, rather than a separate flag, because a flag can
# disagree with them — and the failure that produces is uploads vanishing into
# a bucket nobody configured.
_USE_S3 = bool(AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID)

STORAGES = {
    "default": {
        "BACKEND": (
            "storages.backends.s3boto3.S3Boto3Storage" if _USE_S3
            else "django.core.files.storage.FileSystemStorage"
        )
    },
    "staticfiles": {
        # Hashed filenames: `design-system.css` is collected as
        # `design-system.a1b2c3d4.css`, and `{% static %}` emits that name.
        #
        # The plain StaticFilesStorage that was here served every asset under
        # its own unchanging URL, so a browser that had cached the old CSS kept
        # using it after a deploy — the page came back with new markup and old
        # styling, which is exactly the "why is this laid out wrong" report
        # that has no server-side explanation. A changed file now has a changed
        # URL, so there is nothing to invalidate.
        #
        # Manifest, not plain hashing: it also rewrites urls inside CSS, so
        # `url(images/marker.png)` in Leaflet's stylesheet points at the hashed
        # copy rather than 404-ing.
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    }
}
