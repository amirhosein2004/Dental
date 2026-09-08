import os

from celery import Celery

# Same DJANGO_ENV switch the web process uses. Hard-coding `base` here meant
# the worker ran with no environment's overrides at all — SQLite in
# production, and none of the security settings.
_env = os.environ.get('DJANGO_ENV', 'develop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'config.settings.{_env}')

app = Celery('Dental')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()