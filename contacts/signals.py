# -*- coding: utf-8 -*-
"""
Сигналы для приложения contacts.
Автоматическое создание пользователей для контактов с email.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Contact
import re


@receiver(post_save, sender=Contact)
def create_user_for_contact(sender, instance, created, **kwargs):
    """
    Автоматически создает User для Contact, если у Contact есть email и нет связанного User.
    Email используется как username для входа в систему.
    """
    # Если у контакта есть email и нет связанного пользователя
    if instance.email and not instance.user:
        email = instance.email.strip().lower()
        
        # Проверяем, существует ли уже пользователь с таким email
        try:
            existing_user = User.objects.get(email=email)
            # Если пользователь существует, связываем его с контактом
            instance.user = existing_user
            instance.save(update_fields=['user'])
            return
        except User.DoesNotExist:
            pass
        
        # Генерируем username из email (убираем @ и домен)
        username_base = email.split('@')[0]
        username = username_base
        
        # Проверяем, не занят ли username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1
        
        # Создаем пользователя со стандартным паролем
        # Стандартный пароль: Chat2026 - пользователи должны будут сменить его при первом входе
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password='Chat2026',  # Стандартный пароль для всех сотрудников
                is_active=True,
                first_name=instance.full_name.split()[0] if instance.full_name else '',
                last_name=' '.join(instance.full_name.split()[1:]) if len(instance.full_name.split()) > 1 else '',
            )
            
            # Связываем пользователя с контактом
            instance.user = user
            instance.save(update_fields=['user'])
        except Exception as e:
            # Логируем ошибку, но не прерываем сохранение контакта
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при создании пользователя для контакта {instance.id}: {str(e)}")
