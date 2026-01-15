from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from image_cropping import ImageCroppingMixin
from ckeditor.widgets import CKEditorWidget
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Department, Division, Position, Room, Contact, Vacancy


# Ресурсы для импорта/экспорта
class DepartmentResource(resources.ModelResource):
    """Ресурс для импорта/экспорта департаментов"""
    class Meta:
        model = Department
        fields = ('id', 'name_ru', 'name_kk', 'type', 'display_order', 'description')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    """
    Административный интерфейс для управления департаментами.
    """
    list_display = ('name_ru', 'name_kk', 'type', 'display_order', 'get_divisions_count', 'created_at')
    list_editable = ('display_order',)
    list_filter = ('type', 'created_at')
    search_fields = ('name_ru', 'name_kk', 'description')
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name_ru', 'name_kk', 'type'),
            'description': _('Департамент - основное подразделение организации. Руководство - верхний уровень управления.')
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения департамента в списке. Меньшее число = выше в списке.')
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
    resource_class = DepartmentResource
    
    def get_divisions_count(self, obj):
        """Количество отделов в департаменте"""
        return obj.divisions.count()
    get_divisions_count.short_description = _('Количество отделов')


class DivisionResource(resources.ModelResource):
    """Ресурс для импорта/экспорта отделов"""
    class Meta:
        model = Division
        fields = ('id', 'name_ru', 'name_kk', 'department', 'display_order', 'description')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Division)
class DivisionAdmin(ImportExportModelAdmin):
    """
    Административный интерфейс для управления отделами.
    """
    list_display = ('name_ru', 'name_kk', 'department', 'display_order', 'get_contacts_count', 'created_at')
    list_editable = ('display_order',)
    list_filter = ('department', 'created_at')
    search_fields = ('name_ru', 'name_kk', 'description', 'department__name_ru', 'department__name_kk')
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name_ru', 'name_kk', 'department'),
            'description': _('Отдел может принадлежать департаменту или быть независимым.')
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения отдела в списке. Меньшее число = выше в списке.')
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
    autocomplete_fields = ['department']
    resource_class = DivisionResource
    
    def get_contacts_count(self, obj):
        """Количество сотрудников в отделе"""
        return obj.contacts.count()
    get_contacts_count.short_description = _('Количество сотрудников')


class PositionResource(resources.ModelResource):
    """Ресурс для импорта/экспорта должностей"""
    class Meta:
        model = Position
        fields = ('id', 'name_ru', 'name_kk', 'description')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Position)
class PositionAdmin(ImportExportModelAdmin):
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
    resource_class = PositionResource


class RoomResource(resources.ModelResource):
    """Ресурс для импорта/экспорта кабинетов"""
    class Meta:
        model = Room
        fields = ('id', 'number', 'description', 'floor', 'building')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin):
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
    resource_class = RoomResource


class ContactResource(resources.ModelResource):
    """Ресурс для импорта/экспорта контактов"""
    class Meta:
        model = Contact
        fields = ('id', 'full_name', 'department', 'division', 'position', 'room', 
                  'employment_type', 'work_phone', 'mobile_phone', 'email', 
                  'display_order', 'notes')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Contact)
class ContactAdmin(ImageCroppingMixin, ImportExportModelAdmin):
    """
    Административный интерфейс для управления сотрудниками.
    """
    list_display = ('avatar_thumbnail', 'full_name', 'room', 'position', 'division', 'department', 'employment_type', 'display_order', 'work_phone')
    list_editable = ('display_order',)  # Позволяет редактировать порядок прямо в списке
    list_filter = ('employment_type', 'division', 'department', 'position', 'room', 'created_at')
    search_fields = (
        'full_name', 
        'work_phone', 
        'mobile_phone',
        'room__number',
        'position__name_ru',
        'position__name_kk',
        'division__name_ru',
        'division__name_kk',
        'department__name_ru',
        'department__name_kk'
    )
    list_per_page = 50
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('full_name', 'avatar', 'avatar_cropping', 'employment_type', 'division', 'department', 'position', 'room')
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
    resource_class = ContactResource
    
    # Автозаполнение для удобства
    autocomplete_fields = ['division', 'department', 'position', 'room']
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
            "requirements_and_conditions_ru": CKEditorWidget(),
            "requirements_and_conditions_kk": CKEditorWidget(),
        }


class VacancyResource(resources.ModelResource):
    """Ресурс для импорта/экспорта вакансий"""
    class Meta:
        model = Vacancy
        fields = ('id', 'position', 'division', 'department', 'is_active', 
                  'description_ru', 'description_kk', 
                  'requirements_and_conditions_ru', 'requirements_and_conditions_kk',
                  'contact_info', 'display_order')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Vacancy)
class VacancyAdmin(ImportExportModelAdmin):
    """
    Административный интерфейс для управления вакансиями.
    """
    form = VacancyAdminForm
    list_display = ('position', 'department', 'is_active', 'display_order', 'created_at')
    list_filter = ('is_active', 'department', 'position', 'created_at')
    list_editable = ('is_active', 'display_order')
    search_fields = ('position__name_ru', 'position__name_kk', 'description_ru', 'description_kk')
    list_per_page = 50

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('position', 'division', 'department', 'is_active')
        }),
        (_('Описание'), {
            'fields': ('description_ru', 'description_kk')
        }),
        (_('Требования и условия'), {
            'fields': ('requirements_and_conditions_ru', 'requirements_and_conditions_kk')
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


