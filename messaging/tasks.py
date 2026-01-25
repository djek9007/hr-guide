# -*- coding: utf-8 -*-
from celery import shared_task
from django.utils import timezone
import os
from .models import FileAttachment


@shared_task
def delete_old_files():
    """
    Удаляет вложения, у которых delete_after <= сейчас (обычно 30 дней после загрузки).
    Сначала удаляется файл с диска, затем запись в БД. Сообщение (Message) не удаляется,
    у него просто станет attachments=[], чат не падает.
    Запускается ежедневно в 2:00 через Celery Beat.
    """
    old_files = FileAttachment.objects.filter(delete_after__lte=timezone.now())
    
    deleted_count = 0
    for file_attachment in old_files:
        try:
            # Удаляем файл с диска
            if file_attachment.file and os.path.isfile(file_attachment.file.path):
                os.remove(file_attachment.file.path)
            # Удаляем запись из базы данных
            file_attachment.delete()
            deleted_count += 1
        except Exception as e:
            # Логируем ошибку, но продолжаем обработку
            print(f"Error deleting file {file_attachment.id}: {e}")
    
    return f"Deleted {deleted_count} old files"
