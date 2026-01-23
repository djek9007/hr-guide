# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from contacts.models import Contact


class Chat(models.Model):
    """
    Модель для чата между двумя пользователями.
    """
    # Участники чата
    participant1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_participant1',
        verbose_name=_('Участник 1'),
        db_index=True
    )
    
    participant2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_participant2',
        verbose_name=_('Участник 2'),
        db_index=True
    )
    
    # Дата создания чата
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания'),
        db_index=True
    )
    
    # Дата последнего сообщения (для сортировки)
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата последнего сообщения'),
        db_index=True
    )
    
    # Флаг активности чата
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активен'),
        help_text=_('Активен ли чат')
    )

    class Meta:
        verbose_name = _('Чат')
        verbose_name_plural = _('Чаты')
        ordering = ['-last_message_at', '-created_at']
        # Уникальность: один чат между двумя пользователями
        unique_together = [['participant1', 'participant2']]
        indexes = [
            models.Index(fields=['participant1', 'participant2']),
            models.Index(fields=['last_message_at']),
        ]

    def __str__(self):
        return f"Чат: {self.participant1.username} ↔ {self.participant2.username}"
    
    def get_other_participant(self, user):
        """Возвращает другого участника чата"""
        if user == self.participant1:
            return self.participant2
        return self.participant1
    
    def get_other_participant_contact(self, user):
        """Возвращает Contact другого участника"""
        other_user = self.get_other_participant(user)
        try:
            return other_user.contact
        except Contact.DoesNotExist:
            return None


class Message(models.Model):
    """
    Модель для сообщений в чате.
    """
    # Чат, к которому относится сообщение
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Чат'),
        db_index=True
    )
    
    # Отправитель сообщения
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('Отправитель'),
        db_index=True
    )
    
    # Текст сообщения
    text = models.TextField(
        verbose_name=_('Текст сообщения'),
        blank=True,
        null=True
    )
    
    # Дата и время отправки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата отправки'),
        db_index=True
    )
    
    # Флаг прочитанности
    is_read = models.BooleanField(
        default=False,
        verbose_name=_('Прочитано'),
        db_index=True
    )
    
    # Дата прочтения
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Дата прочтения')
    )

    class Meta:
        verbose_name = _('Сообщение')
        verbose_name_plural = _('Сообщения')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"Сообщение от {self.sender.username} в чате {self.chat.id}"


class FileAttachment(models.Model):
    """
    Модель для файлов, прикрепленных к сообщениям.
    Автоматически удаляется через 30 дней.
    """
    # Сообщение, к которому прикреплен файл
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Сообщение'),
        db_index=True
    )
    
    # Файл
    file = models.FileField(
        upload_to='chat_files/%Y/%m/%d/',
        verbose_name=_('Файл'),
        help_text=_('Файл будет автоматически удален через 30 дней')
    )
    
    # Оригинальное имя файла
    original_filename = models.CharField(
        max_length=255,
        verbose_name=_('Оригинальное имя файла')
    )
    
    # Размер файла в байтах
    file_size = models.BigIntegerField(
        verbose_name=_('Размер файла (байты)')
    )
    
    # MIME-тип файла
    mime_type = models.CharField(
        max_length=100,
        verbose_name=_('MIME-тип'),
        blank=True,
        null=True
    )
    
    # Дата загрузки
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата загрузки'),
        db_index=True
    )
    
    # Дата удаления (для Celery задачи)
    delete_after = models.DateTimeField(
        verbose_name=_('Удалить после'),
        help_text=_('Дата, после которой файл будет удален (30 дней после загрузки)'),
        db_index=True
    )

    class Meta:
        verbose_name = _('Вложение')
        verbose_name_plural = _('Вложения')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['message', 'uploaded_at']),
            models.Index(fields=['delete_after']),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.message.id})"
