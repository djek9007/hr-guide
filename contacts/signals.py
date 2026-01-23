# -*- coding: utf-8 -*-
"""
Сигналы для приложения contacts.
Автоматическое создание пользователей для контактов с email.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from .models import Contact
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Contact)
def check_email_change(sender, instance, **kwargs):
    """
    Сохраняем старый email и пользователя перед сохранением для проверки изменений.
    """
    if instance.pk:
        try:
            old_instance = Contact.objects.get(pk=instance.pk)
            instance._old_email = old_instance.email
            instance._old_user = old_instance.user
        except Contact.DoesNotExist:
            instance._old_email = None
            instance._old_user = None
    else:
        instance._old_email = None
        instance._old_user = None


@receiver(post_save, sender=Contact)
def create_user_for_contact(sender, instance, created, **kwargs):
    """
    Автоматически создает User для Contact, если у Contact есть email и нет связанного User.
    Email используется как username для входа в систему.
    """
    # Пропускаем, если пользователь уже связан
    if instance.user:
        return
    
    # Если у контакта нет email, пропускаем
    if not instance.email or not instance.email.strip():
        return
    
    # Проверяем, нужно ли создавать пользователя
    # Если это обновление существующего контакта, проверяем изменения
    if not created:
        old_user = getattr(instance, '_old_user', None)
        old_email = getattr(instance, '_old_email', None)
        
        # Если пользователь был удален (был, но теперь нет) - создаем нового
        if old_user and not instance.user:
            # Пользователь был удален - создаем нового
            logger.info(f"Пользователь был удален для контакта {instance.full_name}, создаем нового")
        # Если email был добавлен или изменился - создаем пользователя
        elif (not old_email and instance.email) or (old_email and old_email != instance.email):
            # Email был добавлен или изменился - создаем пользователя
            logger.info(f"Email был добавлен или изменился для контакта {instance.full_name}, создаем пользователя")
        # Если email не изменился и пользователя не было - пропускаем (чтобы не создавать при каждом сохранении)
        elif old_email and old_email == instance.email and not old_user:
            # Email не изменился и пользователя не было - пропускаем
            logger.debug(f"Email не изменился и пользователя не было для контакта {instance.full_name}, пропускаем")
            return
        # В остальных случаях тоже создаем (на всякий случай)
        else:
            logger.info(f"Создаем пользователя для контакта {instance.full_name} (обновление)")
    
    # Если у контакта есть email и нет связанного пользователя - создаем
    if instance.email and not instance.user:
        email = instance.email.strip().lower()
        
        if not email:
            return
        
        try:
            with transaction.atomic():
                # Проверяем, существует ли уже пользователь с таким email
                try:
                    existing_user = User.objects.get(email=email)
                    # Если пользователь существует, связываем его с контактом
                    Contact.objects.filter(pk=instance.pk).update(user=existing_user)
                    logger.info(f"Связан существующий пользователь {existing_user.username} с контактом {instance.full_name}")
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
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='Chat2026',  # Стандартный пароль для всех сотрудников
                    is_active=True,
                    first_name=instance.full_name.split()[0] if instance.full_name else '',
                    last_name=' '.join(instance.full_name.split()[1:]) if len(instance.full_name.split()) > 1 else '',
                )
                
                # Связываем пользователя с контактом (используем update для избежания рекурсии)
                Contact.objects.filter(pk=instance.pk).update(user=user)
                logger.info(f"Создан пользователь {username} для контакта {instance.full_name} (email: {email})")
                
        except Exception as e:
            # Логируем ошибку, но не прерываем сохранение контакта
            logger.error(f"Ошибка при создании пользователя для контакта {instance.id} ({instance.full_name}): {str(e)}", exc_info=True)
