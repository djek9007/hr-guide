# -*- coding: utf-8 -*-
"""
Context-процессоры для шаблонов.

user_display_name — добавляет в контекст отображаемое ФИО авторизованного
пользователя (из Contact.full_name, User.get_full_name или username).
"""
from contacts.models import Contact


def user_display_name(request):
    """
    Добавляет в контекст шаблона user_display_name — ФИО или имя для отображения
    в шапке (кто авторизован). Приоритет: Contact.full_name → get_full_name → username.
    """
    if request.user.is_authenticated:
        name = request.user.get_full_name() or request.user.username
        try:
            if request.user.contact.full_name:
                name = request.user.contact.full_name
        except Contact.DoesNotExist:
            pass
        return {'user_display_name': name}
    return {}
