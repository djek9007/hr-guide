# -*- coding: utf-8 -*-
import os
from celery import Celery

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_guide.settings')

# Создаем экземпляр Celery
app = Celery('hr_guide')

# Загружаем настройки из Django settings с префиксом CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в приложениях Django
app.autodiscover_tasks()
