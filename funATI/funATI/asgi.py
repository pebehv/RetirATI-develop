"""
ASGI config for funATI project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import funATIAPP.routing
from funATIAPP.middleware import QueryAuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'funATI.settings')

# Initialize Django BEFORE importing models
django.setup()

# Get the Django ASGI application early for use in mixed protocol routing
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        QueryAuthMiddlewareStack(
            URLRouter(
                funATIAPP.routing.websocket_urlpatterns
            )
        )
    ),
})
