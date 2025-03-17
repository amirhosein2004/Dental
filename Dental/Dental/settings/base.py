import os
from pathlib import Path
from dotenv import load_dotenv
import secrets

# بارگذاری فایل .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# متغیرهای محیطی عمومی
SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_urlsafe(50))  # مقدار پیش‌فرض برای مواقع تست

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'home',
    'blog',
    'django_jalali',
    'users',
    'about',
    'core',
    'service',
    'gallery',
    'contact',
    'dashboard',
    'accounts',

    # Third-party apps
    'django_filters',  # Django filters for querysets
    'captcha',  # Django reCAPTCHA integration
    'django_cleanup.apps.CleanupConfig',  # Django clean up module for removing suspended files
    'django_ckeditor_5',  # Django CKEditor 5 integration

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Dental.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
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

WSGI_APPLICATION = 'Dental.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Dental/settings/base.py
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # دیتابیس شماره 1
    }
}


# تنظیمات Redis به‌عنوان بروکر برای Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # آدرس Redis (پیش‌فرض localhost و پورت 6379)
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'  # برای ذخیره نتایج تسک‌ها
CELERY_ACCEPT_CONTENT = ['json']  # فرمت داده‌های قابل قبول
CELERY_TASK_SERIALIZER = 'json'   # سریالایزر تسک‌ها
CELERY_RESULT_SERIALIZER = 'json' # سریالایزر نتایج
# تنظیمات Celery برای تلاش مجدد اتصال بروکر در زمان راه‌اندازی
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


PASSWORD_RESET_TIMEOUT = 1800  # ۳۰ دقیقه (۱۸۰۰ ثانیه)

LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'en-us')
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = os.getenv('USE_I18N', 'False') == 'True'
USE_TZ = os.getenv('USE_TZ', 'False') == 'True'

MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / os.getenv('MEDIA_ROOT', 'media')

STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATIC_ROOT = BASE_DIR / os.getenv('STATIC_ROOT', 'static')

 
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Google ReCaptcha
RECAPTCHA_PUBLIC_KEY = "6LdwEtsqAAAAADzdwgPOrMVPUbbMkKfkyqMIcr55"
RECAPTCHA_PRIVATE_KEY = "6LdwEtsqAAAAAGmybZkNo-FV-hCmaLsbCc9dpwg3"

# email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'amirhoosenbabai82@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', None)

OTP_SECRET_KEY = os.getenv('OTP_SECRET_KEY', secrets.token_urlsafe(50))
RESET_PREFIX = os.getenv('RESET_PREFIX', 'amir-amiir-amiiir')

# SESSION_COOKIE_SECURE = True  # فقط HTTPS
# SESSION_COOKIE_HTTPONLY = True  # جلوگیری از دسترسی جاوااسکریپت
# SESSION_COOKIE_SAMESITE = 'Strict'  # جلوگیری از CSRF
# CSRF_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True  # همه درخواست‌ها به HTTPS ریدایرکت بشن


CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'link', 'bulletedList', 
            'numberedList', 'blockQuote', 'imageUpload', 'undo', 'redo',
            'fontColor', 'fontBackgroundColor'  # اضافه کردن گزینه‌های رنگ
        ],
        'language': 'fa',  
        'height': '300px',
        'width': '100%',
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
        'fontColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 0%)', 'label': 'Black'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'Dim gray'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'Gray'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'Light gray'},
                {'color': 'hsl(0, 0%, 100%)', 'label': 'White'},
                {'color': 'hsl(0, 75%, 60%)', 'label': 'Red'},
                {'color': 'hsl(30, 75%, 60%)', 'label': 'Orange'},
                {'color': 'hsl(60, 75%, 60%)', 'label': 'Yellow'},
                {'color': 'hsl(120, 75%, 60%)', 'label': 'Green'},
                {'color': 'hsl(180, 75%, 60%)', 'label': 'Cyan'},
                {'color': 'hsl(240, 75%, 60%)', 'label': 'Blue'},
                {'color': 'hsl(300, 75%, 60%)', 'label': 'Purple'}
            ],
            'columns': 5
        },
        'fontBackgroundColor': {
            'colors': [
                {'color': 'hsl(0, 0%, 100%)', 'label': 'White'},
                {'color': 'hsl(0, 0%, 90%)', 'label': 'Light gray'},
                {'color': 'hsl(0, 0%, 60%)', 'label': 'Gray'},
                {'color': 'hsl(0, 0%, 30%)', 'label': 'Dim gray'},
                {'color': 'hsl(0, 0%, 0%)', 'label': 'Black'},
                {'color': 'hsl(0, 75%, 85%)', 'label': 'Light red'},
                {'color': 'hsl(30, 75%, 85%)', 'label': 'Light orange'},
                {'color': 'hsl(60, 75%, 85%)', 'label': 'Light yellow'},
                {'color': 'hsl(120, 75%, 85%)', 'label': 'Light green'},
                {'color': 'hsl(180, 75%, 85%)', 'label': 'Light cyan'},
                {'color': 'hsl(240, 75%, 85%)', 'label': 'Light blue'},
                {'color': 'hsl(300, 75%, 85%)', 'label': 'Light purple'}
            ],
            'columns': 5
        },
        'language': 'fa',
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
    },
}

