# -*- coding: utf-8 -*-
"""
Сигналы для приложения contacts.
Автоматическое создание пользователей для контактов с email.
"""
from django.db.models.signals import post_save, pre_save, pre_delete
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
    logger.info(f"Сигнал create_user_for_contact вызван для контакта {instance.id} ({instance.full_name}), created={created}")
    
    # Пропускаем, если пользователь уже связан
    if instance.user:
        logger.debug(f"Пользователь уже связан с контактом {instance.full_name}, пропускаем")
        return
    
    # Если у контакта нет email, пропускаем
    if not instance.email or not instance.email.strip():
        logger.debug(f"У контакта {instance.full_name} нет email, пропускаем")
        return
    
    # Упрощенная логика: если есть email и нет пользователя - всегда создаем
    # Это работает и для новых контактов, и для обновлений (включая случай, когда пользователь был удален)
    logger.info(f"Создаем пользователя для контакта {instance.full_name} (email: {instance.email})")
    
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
                    # Обновляем instance
                    instance.user = existing_user
                    instance.refresh_from_db()
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
                # Обновляем instance, чтобы он знал о новом пользователе
                instance.user = user
                instance.refresh_from_db()
                logger.info(f"Создан пользователь {username} для контакта {instance.full_name} (email: {email})")
                
        except Exception as e:
            # Логируем ошибку, но не прерываем сохранение контакта
            logger.error(f"Ошибка при создании пользователя для контакта {instance.id} ({instance.full_name}): {str(e)}", exc_info=True)


@receiver(pre_delete, sender=Contact)
def delete_user_for_contact(sender, instance, **kwargs):
    """
    Удаляет связанного пользователя при удалении контакта.
    """
    if instance.user:
        try:
            user = instance.user
            username = user.username
            email = user.email
            
            # Удаляем пользователя
            user.delete()
            logger.info(f"Удален пользователь {username} (email: {email}) при удалении контакта {instance.full_name}")
        except Exception as e:
            # Логируем ошибку, но не прерываем удаление контакта
            logger.error(f"Ошибка при удалении пользователя для контакта {instance.id} ({instance.full_name}): {str(e)}", exc_info=True)
