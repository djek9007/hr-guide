# -*- coding: utf-8 -*-
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import FileAttachment


@receiver(pre_save, sender=FileAttachment)
def set_delete_after_date(sender, instance, **kwargs):
    """
    Автоматически устанавливает дату удаления файла (30 дней после загрузки).
    """
    if not instance.delete_after:
        instance.delete_after = timezone.now() + timedelta(days=30)
