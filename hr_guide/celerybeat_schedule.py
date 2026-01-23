# -*- coding: utf-8 -*-
"""
Конфигурация расписания для Celery Beat (периодические задачи).
"""
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'delete-old-chat-files': {
        'task': 'messaging.tasks.delete_old_files',
        'schedule': crontab(hour=2, minute=0),  # Каждый день в 2:00 ночи
        # Альтернативно можно использовать:
        # 'schedule': 86400.0,  # Каждые 24 часа (в секундах)
    },
}
