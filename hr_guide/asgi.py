"""
ASGI config for hr_guide project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_guide.settings')

# Инициализируем Django ASGI приложение ПЕРВЫМ
django_asgi_app = get_asgi_application()

# Импортируем routing ПОСЛЕ инициализации Django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import messaging.routing

# Загружаем URL patterns после инициализации Django
websocket_urlpatterns = messaging.routing.get_websocket_urlpatterns()

# Настраиваем ASGI для поддержки WebSocket через Channels
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
