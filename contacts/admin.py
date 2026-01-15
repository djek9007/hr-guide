from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from image_cropping import ImageCroppingMixin
from ckeditor.widgets import CKEditorWidget
from .models import Department, Position, Room, Contact, Vacancy


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления отделами.
    """
    list_display = ('name_ru', 'name_kk', 'parent', 'display_order', 'created_at')
    list_editable = ('display_order',)  # Позволяет редактировать порядок прямо в списке
    list_filter = ('parent', 'created_at')
    search_fields = ('name_ru', 'name_kk', 'description')
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name_ru', 'name_kk', 'parent')
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения отдела в списке. Меньшее число = выше в списке. Если не указано, сортировка по алфавиту.')
        }),
        (_('Описание'), {
            'fields': ('description',)
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления должностями.
    """
    list_display = ('name_ru', 'name_kk', 'created_at')
    search_fields = ('name_ru', 'name_kk', 'description')
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name_ru', 'name_kk')
        }),
        (_('Описание'), {
            'fields': ('description',)
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления кабинетами.
    """
    list_display = ('number', 'description', 'floor', 'building', 'created_at')
    list_filter = ('floor', 'building', 'created_at')
    search_fields = ('number', 'description', 'building')
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('number', 'description')
        }),
        (_('Расположение'), {
            'fields': ('floor', 'building')
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Contact)
class ContactAdmin(ImageCroppingMixin, admin.ModelAdmin):
    """
    Административный интерфейс для управления контактами.
    """
    list_display = ('avatar_thumbnail', 'full_name', 'room', 'position', 'department', 'display_order', 'work_phone')
    list_editable = ('display_order',)  # Позволяет редактировать порядок прямо в списке
    list_filter = ('department', 'position', 'room', 'created_at')
    search_fields = (
        'full_name', 
        'work_phone', 
        'mobile_phone',
        'room__number',
        'position__name_ru',
        'position__name_kk',
        'department__name_ru',
        'department__name_kk'
    )
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('full_name', 'avatar', 'avatar_cropping', 'department', 'position', 'room')
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения сотрудника в списке. Меньшее число = выше в списке. Если не указано, сортировка по алфавиту.')
        }),
        (_('Контакты'), {
            'fields': ('work_phone', 'mobile_phone', 'email')
        }),
        (_('Дополнительно'), {
            'fields': ('notes',)
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Автозаполнение для удобства
    autocomplete_fields = ['department', 'position', 'room']
    list_display_links = ('full_name',)
    
    def avatar_thumbnail(self, obj):
        """Отображение миниатюры аватарки в списке"""
        if obj.avatar:
            return format_html(
                '<div style="display: flex; justify-content: center; align-items: center;"><img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" /></div>',
                obj.avatar.url
            )
        return format_html(
            '<div style="display: flex; justify-content: center; align-items: center;"><div style="width: 40px; height: 40px; border-radius: 50%; background: #e5e7eb; display: flex; align-items: center; justify-content: center;"><i class="fas fa-user" style="color: #9ca3af;"></i></div></div>'
        )
    avatar_thumbnail.short_description = _('Аватарка')
    avatar_thumbnail.allow_tags = True
    
    class Media:
        css = {
            'all': ('admin/css/avatar_center.css',)
        }
    
    def get_list_display(self, request):
        """Переопределяем для добавления стилей центрирования"""
        return self.list_display
    
    # Переводим названия полей для админки
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Все поля уже используют verbose_name с _(), так что переводы применятся автоматически
        return form


class VacancyAdminForm(forms.ModelForm):
    """Форма вакансии с подключенным CKEditor."""

    class Meta:
        model = Vacancy
        fields = "__all__"
        widgets = {
            # Подключаем CKEditor к основным текстовым полям
            "description_ru": CKEditorWidget(),
            "description_kk": CKEditorWidget(),
            "requirements_ru": CKEditorWidget(),
            "requirements_kk": CKEditorWidget(),
            "conditions_ru": CKEditorWidget(),
            "conditions_kk": CKEditorWidget(),
        }


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    """
    Административный интерфейс для управления вакансиями.
    """
    form = VacancyAdminForm
    list_display = ('title_ru', 'title_kk', 'department', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'department', 'created_at')
    list_editable = ('is_active', 'display_order')
    search_fields = ('title_ru', 'title_kk', 'description_ru', 'description_kk')
    list_per_page = 50

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('title_ru', 'title_kk', 'department', 'is_active')
        }),
        (_('Описание'), {
            'fields': ('description_ru', 'description_kk')
        }),
        (_('Требования'), {
            'fields': ('requirements_ru', 'requirements_kk')
        }),
        (_('Условия работы'), {
            'fields': ('conditions_ru', 'conditions_kk')
        }),
        (_('Контактная информация'), {
            'fields': ('contact_info',)
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения вакансии в списке. Меньшее число = выше в списке. Если не указано, сортировка по дате создания.')
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


