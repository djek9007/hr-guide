# -*- coding: utf-8 -*-
# Это гарантирует, что Celery приложение загружается при запуске Django
try:
    from .celery import app as celery_app
except ImportError:
    # Allow running management commands locally without celery installed
    celery_app = None

__all__ = ('celery_app',)
