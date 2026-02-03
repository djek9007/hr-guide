# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from contacts.models import Contact


class Chat(models.Model):
    """
    Модель для чата (личного или группового).
    """
    TYPE_PRIVATE = 'private'
    TYPE_GROUP = 'group'
    
    CHAT_TYPE_CHOICES = [
        (TYPE_PRIVATE, _('Личный чат')),
        (TYPE_GROUP, _('Групповой чат')),
    ]

    # Тип чата
    type = models.CharField(
        max_length=10,
        choices=CHAT_TYPE_CHOICES,
        default=TYPE_PRIVATE,
        verbose_name=_('Тип чата')
    )
    
    # Название (для групповых чатов)
    title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Название группы')
    )
    
    # Аватар (для групповых чатов)
    avatar = models.ImageField(
        upload_to='chat_avatars/',
        blank=True,
        null=True,
        verbose_name=_('Аватар группы')
    )

    # Создатель (владелец) группы
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_chats',
        verbose_name=_('Создатель')
    )

    # Участники чата (deprecated, use ChatParticipant)
    participant1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_participant1',
        verbose_name=_('Участник 1'),
        db_index=True,
        null=True,
        blank=True
    )
    
    participant2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_participant2',
        verbose_name=_('Участник 2'),
        db_index=True,
        null=True,
        blank=True
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
        indexes = [
            models.Index(fields=['last_message_at']),
        ]

    def __str__(self):
        if self.type == self.TYPE_GROUP:
            return f"Группа: {self.title}"
        p1 = self.participant1.username if self.participant1 else "Unknown"
        p2 = self.participant2.username if self.participant2 else "Unknown"
        return f"Чат: {p1} ↔ {p2}"
    
    def get_other_participant(self, user):
        """
        Возвращает другого участника чата (только для личных чатов).
        Для совместимости.
        """
        if self.type == self.TYPE_GROUP:
            return None
        if user == self.participant1:
            return self.participant2
        return self.participant1
    
    def get_other_participant_contact(self, user):
        """Возвращает Contact другого участника"""
        other_user = self.get_other_participant(user)
        if other_user:
            try:
                return other_user.contact
            except Contact.DoesNotExist:
                return None
        return None


class ChatParticipant(models.Model):
    """
    Участник чата.
    """
    ROLE_MEMBER = 'member'
    ROLE_ADMIN = 'admin'
    
    ROLE_CHOICES = [
        (ROLE_MEMBER, _('Участник')),
        (ROLE_ADMIN, _('Администратор')),
    ]

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('Чат')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_participations',
        verbose_name=_('Пользователь')
    )
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
        verbose_name=_('Роль')
    )
    
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата присоединения')
    )

    class Meta:
        verbose_name = _('Участник чата')
        verbose_name_plural = _('Участники чата')
        unique_together = [['chat', 'user']]
        indexes = [
            models.Index(fields=['chat', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} в {self.chat}"


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
