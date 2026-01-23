# -*- coding: utf-8 -*-
from django.urls import re_path

# Ленивая загрузка consumers для избежания проблем с AppRegistryNotReady
# Не импортируем consumers на уровне модуля
def get_websocket_urlpatterns():
    from . import consumers
    return [
        re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
    ]
