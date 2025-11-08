"""
ASGI config for messaging project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from comments.routing import websocket_urlpatterns as comments_websocket_urlpatterns
from tickets.routing import websocket_urlpatterns as tickets_websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messaging.settings')

django_asgi_app = get_asgi_application()

# Combine WebSocket URL patterns from all apps
all_websocket_urlpatterns = comments_websocket_urlpatterns + tickets_websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(all_websocket_urlpatterns)
        )
    ),
})
