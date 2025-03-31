import os
from django.core.wsgi import get_wsgi_application

# بررسی متغیر محیطی DJANGO_ENV برای تعیین فایل تنظیمات مناسب
env = os.environ.get('DJANGO_ENV', 'dev')  # پیش‌فرض به 'development' تنظیم می‌شود

# تنظیم ماژول تنظیمات بر اساس مقدار محیطی
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'Dental.settings.{env}')

# ایجاد اپلیکیشن WSGI
application = get_wsgi_application()




# """
# WSGI config for Dental project.

# It exposes the WSGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
# """

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dental.settings')

# application = get_wsgi_application()
