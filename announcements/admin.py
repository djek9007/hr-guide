from django.contrib import admin
from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """
    Административная панель для управления объявлениями.
    
    Обеспечивает:
    - Отображение списка объявлений с ключевыми полями
    - Фильтрацию по дате публикации
    - Поиск по заголовкам и содержимому на обоих языках
    - Группировку полей по языкам в форме редактирования
    - Автоматическую установку автора при создании
    """
    
    list_display = ['title_ru', 'title_kk', 'published_date', 'author', 'is_new']
    list_filter = ['published_date']
    search_fields = ['title_ru', 'title_kk', 'content_ru', 'content_kk']
    readonly_fields = ['author']
    
    fieldsets = (
        ('Русский язык', {
            'fields': ('title_ru', 'content_ru')
        }),
        ('Қазақ тілі', {
            'fields': ('title_kk', 'content_kk')
        }),
        ('Метаданные', {
            'fields': ('published_date', 'author')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Переопределяет сохранение модели для автоматической установки автора.
        
        При создании нового объявления автоматически устанавливает
        текущего пользователя в поле author.
        
        Args:
            request: HTTP запрос с информацией о текущем пользователе
            obj: Объект Announcement для сохранения
            form: Форма с данными объявления
            change: True если редактирование, False если создание
        """
        if not change:  # Если создается новый объект
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def is_new(self, obj):
        """
        Отображает индикатор нового объявления в списке.
        
        Args:
            obj: Объект Announcement
            
        Returns:
            bool: True если объявление создано сегодня, иначе False
        """
        return obj.is_new()
    
    is_new.boolean = True
    is_new.short_description = 'Новое'
