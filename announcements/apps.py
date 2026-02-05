"""
Конфигурация приложения announcements.

Это приложение обеспечивает систему двуязычных объявлений (казахский и русский языки)
для HR-системы с публичным доступом к просмотру и административным интерфейсом
для управления.
"""

from django.apps import AppConfig


class AnnouncementsConfig(AppConfig):
    """
    Конфигурация Django-приложения для системы объявлений.
    
    Attributes:
        default_auto_field: Тип поля для автоматических первичных ключей
        name: Имя приложения
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'announcements'
    verbose_name = 'Система объявлений'
