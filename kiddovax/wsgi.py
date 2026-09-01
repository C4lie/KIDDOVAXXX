"""
WSGI config for kiddovax project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kiddovax.settings')

application = get_wsgi_application()

try:
    from hospitalapp.models import Hospitaltbl
    if Hospitaltbl.objects.count() < 10:
        from django.core.management import call_command
        call_command('seed_db')
except Exception as e:
    print(f"WSGI Auto-seed notice: {e}")
  