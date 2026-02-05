"""
Context processors для приложения announcements.

Предоставляет глобальные переменные контекста для всех шаблонов.
"""

from django.utils import timezone
from .models import Announcement


def new_announcements_count(request):
    """
    Context processor для отображения количества новых объявлений в меню.
    
    Подсчитывает объявления, опубликованные в текущий день.
    Возвращает None, если счетчик равен 0, чтобы не отображать его в шаблоне.
    
    Args:
        request: HTTP запрос Django
    
    Returns:
        dict: Словарь с ключом 'new_announcements_count', содержащим:
              - количество новых объявлений (int), если есть объявления за сегодня
              - None, если новых объявлений нет
    
    Requirements: 5.1, 5.3, 5.4
    """
    today = timezone.now().date()
    count = Announcement.objects.filter(published_date__date=today).count()
    
    return {
        'new_announcements_count': count if count > 0 else None
    }
