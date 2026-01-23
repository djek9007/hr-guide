# -*- coding: utf-8 -*-
# Это гарантирует, что Celery приложение загружается при запуске Django
from .celery import app as celery_app

__all__ = ('celery_app',)
