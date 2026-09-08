"""
ASGI config for Dental project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# `config.settings` is a package, not a settings module — importing it gave
# an empty namespace. Use the same DJANGO_ENV switch as wsgi.py.
_env = os.environ.get('DJANGO_ENV', 'develop')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'config.settings.{_env}')

application = get_asgi_application()
