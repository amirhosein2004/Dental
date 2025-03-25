# Dental/Dental/celery.py

import os
from celery import Celery
from celery.schedules import crontab

# تنظیم متغیر محیطی برای ماژول تنظیمات جنگو
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dental.settings.base')

# ایجاد نمونه Celery
app = Celery('Dental')

# بارگذاری تنظیمات از settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# پیدا کردن خودکار تسک‌ها
app.autodiscover_tasks()

# تنظیمات Celery Beat
app.conf.beat_schedule = {
    'delete-old-messages-every-day': {
        'task': 'contact.tasks.delete_old_messages',  # اسم تسک
        'schedule': crontab(day_of_month='*/5', hour=0, minute=0),        # هر ۵ روز ساعت 00:00 (نصفه‌شب)
        'args': (180,),                                # پیام‌های قدیمی‌تر از 180 روز
    },
}