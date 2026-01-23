# -*- coding: utf-8 -*-
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'
    verbose_name = 'Мессенджер'
    
    def ready(self):
        """Импортируем сигналы при запуске приложения"""
        import messaging.signals
