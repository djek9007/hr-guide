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
    # Пропускаем, если пользователь уже связан
    if instance.user:
        return
    
    # Если у контакта нет email, пропускаем
    if not instance.email or not instance.email.strip():
        return
    
    email = instance.email.strip().lower()
    
    logger.info(f"Обработка пользователя для контакта {instance.full_name} (email: {email})")
    
    # Используем атомарную транзакцию для гарантии целостности
    try:
        with transaction.atomic():
            # 1. Проверяем, существует ли пользователь с таким email
            user = User.objects.filter(email=email).first()
            
            if user:
                # Проверяем, не связан ли пользователь с ДРУГИМ контактом
                # Reverse relation for OneToOneField is 'contact' (raises DoesNotExist if missing)
                try:
                    existing_contact = user.contact
                    if existing_contact and existing_contact.pk != instance.pk:
                        logger.warning(f"Пользователь {email} уже связан с контактом {existing_contact} (id={existing_contact.id}). Нельзя привязать к {instance}.")
                        # Здесь можно выбросить ошибку, чтобы уведомить админа
                        # raise ValueError(f"Email {email} уже используется пользователем, связанным с другим сотрудником.")
                        return 
                except Contact.DoesNotExist:
                    # Пользователь есть, но контакта у него нет -> можно связывать
                    pass
                    
                logger.info(f"Найден существующий свободный пользователь {user.username}")
                
            else:
                # 2. Создаем нового пользователя
                username_base = email.split('@')[0]
                # Очистка username от недопустимых символов, если нужно, но Django допускает многое
                username = username_base
                
                # Обеспечиваем уникальность username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1
                
                # Создаем
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='Chat2026',  # Стандартный пароль
                    is_active=True,
                    first_name=instance.full_name.split()[0] if instance.full_name else '',
                    last_name=' '.join(instance.full_name.split()[1:]) if len(instance.full_name.split()) > 1 else '',
                )
                logger.info(f"Создан новый пользователь {username}")

            # 3. Связываем пользователя с контактом
            # Используем update для обновления в БД без вызова сигналов (рекурсии)
            Contact.objects.filter(pk=instance.pk).update(user=user)
            
            # Обновляем текущий инстанс модели, чтобы последующий код (например, в admin) видел изменения
            instance.user = user
            
    except Exception as e:
        logger.error(f"Критическая ошибка при создании пользователя для {instance}: {e}", exc_info=True)
        # ВАЖНО: пробрасываем ошибку дальше, чтобы она отобразилась в админке
        raise e


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
