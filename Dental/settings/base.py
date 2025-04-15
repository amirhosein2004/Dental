import os
from pathlib import Path
from dotenv import load_dotenv
import secrets

# Load environment variables from a .env file
load_dotenv()

# Define the base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# General environment variables
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(50))  # Default value for testing
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Enable/disable debug mode
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')  # List of allowed hosts

# Installed apps for the Django project
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps
    'home',
    'blog',
    'users',
    'about',
    'core',
    'service',
    'gallery',
    'contact',
    'dashboard',
    'accounts',

    # Third-party apps
    'django_filters',  # For filtering querysets
    'captcha',  # Google reCAPTCHA integration
    'django_ckeditor_5',  # CKEditor 5 integration for rich text editing
    'axes',  # Brute force protection
    'compressor',  # For compressing CSS and JavaScript files
    'storages', # For using cloud storage backends (e.g., AWS S3, Google Cloud Storage)
]

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Axes middleware for brute force protection
    'axes.middleware.AxesMiddleware',
]

# Root URL configuration
ROOT_URLCONF = 'Dental.urls'

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Custom template directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI application
WSGI_APPLICATION = 'Dental.wsgi.application'

# Password validation settings
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

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


# Caching configuration using Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),  # Redis database 1
    }
}

# Celery configuration for task queue
CELERY_BROKER_URL = os.getenv('REDIS_URL_CELERY', 'redis://localhost:6379/0')  # Redis broker
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL_CELERY', 'redis://localhost:6379/0')  # Redis result backend
CELERY_ACCEPT_CONTENT = ['json']  # Accepted content types
CELERY_TASK_SERIALIZER = 'json'  # Task serializer
CELERY_RESULT_SERIALIZER = 'json'  # Result serializer
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True  # Retry broker connection on startup

# Password reset timeout (30 minutes)
PASSWORD_RESET_TIMEOUT = 1800

# Localization settings
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = os.getenv('USE_I18N', 'False') == 'True'
USE_TZ = os.getenv('USE_TZ', 'False') == 'True'

# Static and media file settings
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / os.getenv('STATIC_ROOT', 'staticfiles')
STATICFILES_DIRS = [BASE_DIR / 'static']

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# Google reCAPTCHA keys
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')

# Email configuration
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'amirhoosenbabai82@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)

# OTP and URL settings
OTP_SECRET_KEY = os.getenv('OTP_SECRET_KEY', secrets.token_urlsafe(50))
RESET_PREFIX = os.getenv('RESET_PREFIX', secrets.token_urlsafe(8))
RESET_SUFFIX = os.getenv('RESET_SUFFIX', secrets.token_urlsafe(4))
SECURE_ADMIN_PANEL = os.getenv('SECURE_ADMIN_PANEL', secrets.token_urlsafe(4))

# Axes configuration for brute force protection
AXES_ONLY_ADMIN_SITE = True  # Restrict Axes to admin site only
AXES_FAILURE_LIMIT = 4  # Lock account after 4 failed attempts
AXES_COOLOFF_TIME = 48  # Unlock account after 48 hours
AXES_LOCK_OUT_AT_FAILURE = True  # Enable account lockout
AXES_VERBOSE = True  # Log login attempts

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default authentication backend
]

# CKEditor 5 configuration
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'link', 'bulletedList', 
            'numberedList', 'blockQuote', 'imageUpload', 'undo', 'redo',
            'fontColor', 'fontBackgroundColor'  # گزینه‌های رنگ
        ],
        'language': 'fa',  # زبان فارسی
        'height': '300px',
        'width': '100%',
        'image': {  # تنظیمات مربوط به تصاویر
            'toolbar': [
                'imageTextAlternative', '|',  # متن جایگزین تصویر
                'imageStyle:alignLeft', 'imageStyle:alignCenter', 'imageStyle:alignRight'  # جهت‌گیری تصویر
            ],
            'styles': [
                'alignLeft', 'alignCenter', 'alignRight'  # استایل‌های جهت‌گیری
            ]
        }
    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3', '|',
            'bulletedList', 'numberedList', '|',
            'blockQuote',
        ],
        'toolbar': [
            'heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 
            'underline', 'strikethrough', 'code', 'subscript', 'superscript', 
            'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
            'bulletedList', 'numberedList', 'todoList', '|', 'blockQuote', 
            'imageUpload', '|', 'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 
            'mediaEmbed', 'removeFormat', 'insertTable',
        ],
        'image': {  # تنظیمات کامل برای تصاویر
            'toolbar': [
                'imageTextAlternative', '|',  # متن جایگزین
                'imageStyle:alignLeft', 'imageStyle:alignCenter', 'imageStyle:alignRight',  # جهت‌گیری چپ، وسط، راست
                'imageStyle:full', 'imageStyle:side'  # اندازه کامل یا کناری
            ],
            'styles': [
                'full', 'side', 'alignLeft', 'alignCenter', 'alignRight'  # استایل‌های موجود
            ],
            'resizeOptions': [  # گزینه‌های تغییر اندازه تصویر
                {'name': 'resize:original', 'value': None, 'label': 'Original'},
                {'name': 'resize:50', 'value': '50', 'label': '50%'},
                {'name': 'resize:75', 'value': '75', 'label': '75%'},
                {'name': 'resize:100', 'value': '100', 'label': '100%'}
            ]
        },
        'fontColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 0%)', 'label': 'سیاه'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'خاکستری تیره'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'خاکستری'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'خاکستری روشن'},
                {'color': 'hsl(0, 0%, 100%)', 'label': 'سفید'},
                {'color': 'hsl(0, 75%, 60%)', 'label': 'قرمز'},
                {'color': 'hsl(30, 75%, 60%)', 'label': 'نارنجی'},
                {'color': 'hsl(60, 75%, 60%)', 'label': 'زرد'},
                {'color': 'hsl(120, 75%, 60%)', 'label': 'سبز'},
                {'color': 'hsl(180, 75%, 60%)', 'label': 'فیروزه‌ای'},
                {'color': 'hsl(240, 75%, 60%)', 'label': 'آبی'},
                {'color': 'hsl(300, 75%, 60%)', 'label': 'بنفش'}
            ],
            'columns': 5
        },
        'fontBackgroundColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 100%)', 'label': 'سفید'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'خاکستری روشن'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'خاکستری'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'خاکستری تیره'},
                {'color': 'hsl(0, 0%, 0%)', 'label': 'سیاه'},
                {'color': 'hsl(0, 75%, 85%)', 'label': 'قرمز روشن'},
                {'color': 'hsl(30, 75%, 85%)', 'label': 'نارنجی روشن'},
                {'color': 'hsl(60, 75%, 85%)', 'label': 'زرد روشن'},
                {'color': 'hsl(120, 75%, 85%)', 'label': 'سبز روشن'},
                {'color': 'hsl(180, 75%, 85%)', 'label': 'فیروزه‌ای روشن'},
                {'color': 'hsl(240, 75%, 85%)', 'label': 'آبی روشن'},
                {'color': 'hsl(300, 75%, 85%)', 'label': 'بنفش روشن'}
            ],
            'columns': 5
        },
        'language': 'fa',  # زبان فارسی
        'height': '400px',  # ارتفاع ادیتور
        'width': '100%',   # عرض ادیتور
        'htmlSupport': {
            'allow': [
                {'name': 'p'},
                {'name': 'b'},
                {'name': 'i'},
                {'name': 'u'},
                {'name': 'strong'},
                {'name': 'em'},
                {'name': 'h1'},
                {'name': 'h2'},
                {'name': 'h3'},
                {'name': 'ul'},
                {'name': 'ol'},
                {'name': 'li'},
                {'name': 'a', 'attributes': ['href', 'title']},
                {'name': 'img', 'attributes': ['src', 'alt', 'style']},
                {'name': 'table'},
                {'name': 'tr'},
                {'name': 'td', 'attributes': ['colspan', 'rowspan']},
                {'name': 'th'},
                {'name': 'blockquote'},
                {'name': 'code'},
                {'name': 'pre'},
            ],
            'disallow': [
                {'name': 'script'},
                {'name': 'iframe'},
                {'name': 'style'},
                {'name': 'object'},
                {'name': 'embed'},
            ],
        },
        'table': {  # تنظیمات جدول
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells'
            ]
        }
    }
}

# Static files finders configuration
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',  # Finds static files in the filesystem
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # Finds static files in app directories
    'compressor.finders.CompressorFinder',  # Required for django-compressor to work
]

# # Django Compressor settings
COMPRESS_ENABLED = True  # Enable compression
COMPRESS_OFFLINE = True  # Set to False for development, True for production