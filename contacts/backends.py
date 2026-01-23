# -*- coding: utf-8 -*-
"""
Кастомный backend для аутентификации по email.
Позволяет пользователям входить в систему используя email вместо username.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend для аутентификации по email или username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Аутентифицирует пользователя по email или username.
        
        Args:
            request: HTTP запрос
            username: Может быть username или email
            password: Пароль пользователя
            
        Returns:
            User объект если аутентификация успешна, иначе None
        """
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
        
        try:
            # Пытаемся найти пользователя по email или username
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            # Возвращаем None, чтобы Django попробовал другие backends
            return None
        except User.MultipleObjectsReturned:
            # Если найдено несколько пользователей с одинаковым email,
            # берем первого активного
            user = User.objects.filter(
                Q(username=username) | Q(email=username),
                is_active=True
            ).first()
            if not user:
                return None
        
        # Проверяем пароль
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
