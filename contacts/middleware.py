# -*- coding: utf-8 -*-
"""
Middleware для проверки стандартного пароля и перенаправления на смену пароля.
"""
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib.auth import logout


class RequirePasswordChangeMiddleware:
    """
    Middleware, который проверяет, использует ли пользователь стандартный пароль Chat2026.
    Если да, перенаправляет на страницу смены пароля (кроме страниц смены пароля, выхода и API).
    """
    
    # URL-пути, которые не требуют смены пароля
    EXEMPT_PATHS = [
        'contacts:change_password',
        'logout',
        'login',
    ]
    
    # Префиксы URL, которые не требуют смены пароля (например, API)
    EXEMPT_PREFIXES = [
        '/api/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Проверяем только аутентифицированных пользователей
        if request.user.is_authenticated:
            # Проверяем, не является ли текущий путь исключением
            if not self._is_exempt(request):
                # Проверяем, использует ли пользователь стандартный пароль
                if request.user.check_password('Chat2026'):
                    # Перенаправляем на смену пароля
                    change_password_url = reverse('contacts:change_password')
                    if request.path != change_password_url:
                        return redirect(change_password_url)
        
        response = self.get_response(request)
        return response
    
    def _is_exempt(self, request):
        """Проверяет, является ли текущий путь исключением"""
        # Проверяем префиксы
        for prefix in self.EXEMPT_PREFIXES:
            if request.path.startswith(prefix):
                return True
        
        # Проверяем именованные URL
        try:
            resolver_match = resolve(request.path)
            if resolver_match.url_name in self.EXEMPT_PATHS:
                return True
        except:
            pass
        
        return False
