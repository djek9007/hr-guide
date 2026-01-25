# -*- coding: utf-8 -*-
"""
Context-процессоры для шаблонов.

user_display_name — добавляет в контекст отображаемое ФИО авторизованного
пользователя (из Contact.full_name, User.get_full_name или username).

developer_contacts — контакты разработчика (email, Telegram) из настроек
для ссылки «Связь с разработчиком» в футере и страницы /developer-contact/.
"""
from django.conf import settings
from contacts.models import Contact


def developer_contacts(request):
    """
    Добавляет в контекст developer_email, developer_telegram, developer_name
    и has_developer_contact (True, если задан хотя бы email или Telegram).
    """
    email = getattr(settings, 'DEVELOPER_EMAIL', '') or ''
    telegram = getattr(settings, 'DEVELOPER_TELEGRAM', '') or ''
    name = getattr(settings, 'DEVELOPER_NAME', '') or ''
    return {
        'developer_email': email.strip(),
        'developer_telegram': telegram.strip(),
        'developer_name': name.strip(),
        'has_developer_contact': bool(email.strip() or telegram.strip()),
    }


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
