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

# --- Object storage for uploads ---------------------------------------------
# S3-compatible, so the same four variables cover ArvanCloud, Liara, MinIO or
# AWS itself — only the endpoint and the region change. ArvanCloud is what the
# site uses now:
#
#   AWS_S3_ENDPOINT_URL=https://s3.ir-thr-at1.arvanstorage.ir   (Simin, Tehran)
#   AWS_S3_REGION_NAME=ir-thr-at1
#
# See deploy/env/.env.production.example for the full list and the second
# region.
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')

# boto3 signs every request with SigV4, and SigV4 needs a region string even
# when the endpoint is explicit. Left unset it raises `NoRegionError: You must
# specify a region` on the first upload — from inside botocore, with nothing in
# the traceback naming the setting that is missing.
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME') or None
AWS_S3_SIGNATURE_VERSION = os.getenv('AWS_S3_SIGNATURE_VERSION', 's3v4')

# ArvanCloud serves buckets at `<bucket>.s3.<region>.arvanstorage.ir`, which is
# what boto3 does by default. Overridable because MinIO and some on-premise
# gateways only answer path style (`<endpoint>/<bucket>/<key>`), and against
# those the default fails as a DNS error rather than as an HTTP one.
AWS_S3_ADDRESSING_STYLE = os.getenv('AWS_S3_ADDRESSING_STYLE', 'virtual')

# Set this to serve media through a CDN or a custom bucket domain; the value is
# a bare hostname, no scheme and no trailing slash, and django-storages builds
# every media URL from it. Empty means URLs point straight at the bucket.
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN') or None

AWS_S3_FILE_OVERWRITE = False  # Two uploads named photo.jpg stay two files
AWS_DEFAULT_ACL = None  # Send no ACL header; the bucket's own policy decides

# Plain, permanent URLs instead of time-limited signed ones. This is only
# correct while the bucket is readable by anonymous users — on ArvanCloud that
# is the bucket's access setting, `public`. Leave the bucket private and every
# image on the site 403s.
AWS_QUERYSTRING_AUTH = False

# One day of browser caching for anything served out of the bucket. Media names
# are not content-hashed, so this is the same trade-off nginx makes for the
# local /media/ directory: long enough to matter, short enough that a replaced
# image appears the same day.
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'public, max-age=86400'}

# Uploads go to the bucket when there is a bucket, and to local disk when
# there is not.
#
# The backend used to be S3 unconditionally. With a bucket configured that is
# right — on Liara the container filesystem is ephemeral, and even on a VPS a
# bucket survives the machine. With no bucket it is not: every upload died with
# `EndpointConnectionError: Could not connect to the endpoint URL`, from a
# setting no environment file could change. nginx has served /media/ from disk
# all along, waiting for exactly this.
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
