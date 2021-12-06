import os
import django
from channels.routing import get_default_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swallow.settings")
django.setup()
application = get_default_application()

'''
daphne -b 0.0.0.0 -p 8001 swallow.asgi:application
'''