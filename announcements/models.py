from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.utils import timezone


class Announcement(models.Model):
    """
    Модель для двуязычных объявлений (казахский и русский языки).
    
    Объявления доступны для публичного просмотра без авторизации,
    но создавать, редактировать и удалять их могут только администраторы.
    """
    
    # Заголовки на двух языках
    title_kk = models.CharField(
        max_length=255,
        verbose_name="Заголовок (каз)",
        help_text="Заголовок объявления на казахском языке"
    )
    title_ru = models.CharField(
        max_length=255,
        verbose_name="Заголовок (рус)",
        help_text="Заголовок объявления на русском языке"
    )
    
    # Содержимое с rich text форматированием
    content_kk = RichTextField(
        verbose_name="Содержимое (каз)",
        help_text="Содержимое объявления на казахском языке с форматированием"
    )
    content_ru = RichTextField(
        verbose_name="Содержимое (рус)",
        help_text="Содержимое объявления на русском языке с форматированием"
    )
    
    # Метаданные
    published_date = models.DateTimeField(
        verbose_name="Дата публикации",
        help_text="Дата и время публикации объявления"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        help_text="Автор объявления"
    )
    
    class Meta:
        ordering = ['-published_date']
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        indexes = [
            models.Index(fields=['-published_date'], name='announcement_published_idx'),
        ]
    
    def __str__(self):
        """Строковое представление объявления (используется русский заголовок)"""
        return self.title_ru
    
    def is_new(self):
        """
        Проверяет, является ли объявление новым (опубликовано сегодня).
        
        Returns:
            bool: True, если объявление опубликовано в текущий день, иначе False
        """
        return self.published_date.date() == timezone.now().date()
