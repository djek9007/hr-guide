# -*- coding: utf-8 -*-
"""
Конфигурация приложения contacts.
"""
from django.apps import AppConfig


class ContactsConfig(AppConfig):
    """Конфигурация приложения contacts"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contacts'
    verbose_name = 'Контакты'

    def ready(self):
        """Инициализация сигналов при запуске приложения"""
        import contacts.signals  # noqa
