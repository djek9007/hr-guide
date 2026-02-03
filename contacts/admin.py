from django.contrib import admin, messages
from django import forms
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.http import JsonResponse
from django.urls import path
from image_cropping import ImageCroppingMixin
from ckeditor.widgets import CKEditorWidget
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from .models import Department, Division, Position, Room, Contact, Vacancy
from django_admin_listfilter_dropdown.filters import (
    DropdownFilter, RelatedDropdownFilter, ChoiceDropdownFilter
)
from rangefilter.filters import DateRangeFilter


class SafeForeignKeyWidget(ForeignKeyWidget):
    """
    Виджет для ForeignKey полей, который безопасно обрабатывает отсутствующие значения.
    Если объект не найден, возвращает None вместо выброса исключения.
    """
    def clean(self, value, row=None, **kwargs):
        """Очистка значения с обработкой отсутствующих объектов"""
        # Обрабатываем пустые значения
        if value is None or value == '' or (isinstance(value, str) and value.strip() == ''):
            return None
        
        # Пытаемся преобразовать в число, если это ID
        try:
            # Если значение - число, используем его как ID
            if isinstance(value, (int, float)):
                value = int(value)
            elif isinstance(value, str):
                # Пытаемся преобразовать строку в число
                value = int(value.strip())
        except (ValueError, TypeError):
            # Если не удалось преобразовать, пробуем найти по строковому значению
            pass
        
        try:
            # Пытаемся получить объект через родительский метод
            return super().clean(value, row, **kwargs)
        except Exception as e:
            # Если объект не найден или произошла ошибка, возвращаем None
            # Логируем ошибку для отладки (можно убрать в продакшене)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Не удалось найти объект для значения '{value}': {e}")
            return None


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
    list_display = ('id', 'name_ru', 'name_kk', 'type', 'display_order', 'get_divisions_count', 'created_at')
    list_editable = ('display_order',)
    list_filter = (('type', ChoiceDropdownFilter), ('created_at', DateRangeFilter))
    search_fields = ('name_ru', 'name_kk', 'description')
    list_per_page = 50
    list_display_links = ('name_ru', 'name_kk')
    
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
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _divisions_count=Count('divisions', distinct=True)
        )
        return queryset

    def get_divisions_count(self, obj):
        """Количество управлений в департаменте"""
        return obj._divisions_count
    get_divisions_count.short_description = _('Количество управлений')
    get_divisions_count.admin_order_field = '_divisions_count'


class DivisionResource(resources.ModelResource):
    """Ресурс для импорта/экспорта управлений"""
    class Meta:
        model = Division
        fields = ('id', 'name_ru', 'name_kk', 'department', 'display_order', 'description')
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True


@admin.register(Division)
class DivisionAdmin(ImportExportModelAdmin):
    """
    Административный интерфейс для управления управлениями.
    """
    list_display = ('id', 'name_ru', 'name_kk', 'department', 'display_order', 'get_contacts_count', 'created_at')
    list_editable = ('display_order',)
    list_filter = (('department', RelatedDropdownFilter), ('created_at', DateRangeFilter))
    search_fields = ('name_ru', 'name_kk', 'description', 'department__name_ru', 'department__name_kk')
    list_per_page = 50
    list_display_links = ('name_ru', 'name_kk')
    list_editable =('display_order','department')
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name_ru', 'name_kk', 'department'),
            'description': _('Управление может принадлежать департаменту или быть независимым.')
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения управления в списке. Меньшее число = выше в списке.')
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
    list_select_related = ('department',)
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _contacts_count=Count('contacts', distinct=True)
        )
        return queryset
    
    def get_contacts_count(self, obj):
        """Количество сотрудников в управлении"""
        return obj._contacts_count
    get_contacts_count.short_description = _('Количество сотрудников')
    get_contacts_count.admin_order_field = '_contacts_count'


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
    list_display = ('id', 'name_ru', 'name_kk', 'created_at')
    search_fields = ('name_ru', 'name_kk', 'description')
    list_per_page = 50
    list_display_links = ('name_ru', 'name_kk')
    
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
    list_display = ('id', 'number', 'description', 'floor', 'building', 'created_at')
    list_filter = (
        ('floor', DropdownFilter),
        ('building', DropdownFilter),
        ('created_at', DateRangeFilter)
    )
    search_fields = ('number', 'description', 'building')
    list_per_page = 50
    list_display_links = ('number',)
    
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
    # Настройка виджетов для ForeignKey полей с обработкой отсутствующих значений
    # Используем SafeForeignKeyWidget для безопасной обработки отсутствующих объектов
    department = resources.Field(
        column_name='department',
        attribute='department',
        widget=SafeForeignKeyWidget(Department, 'id')
    )
    division = resources.Field(
        column_name='division',
        attribute='division',
        widget=SafeForeignKeyWidget(Division, 'id')
    )
    position = resources.Field(
        column_name='position',
        attribute='position',
        widget=SafeForeignKeyWidget(Position, 'id')
    )
    room = resources.Field(
        column_name='room',
        attribute='room',
        widget=SafeForeignKeyWidget(Room, 'id')
    )
    
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
    list_display = ('id', 'avatar_thumbnail', 'full_name', 'room', 'position', 'division', 'department',  'display_order', 'work_phone')
    list_editable = ('display_order', 'division', 'department')  # Позволяет редактировать порядок прямо в списке
    list_filter = (
        ('employment_type', ChoiceDropdownFilter),
        ('division', RelatedDropdownFilter),
        ('department', RelatedDropdownFilter),
        ('position', RelatedDropdownFilter),
        ('room', RelatedDropdownFilter),
        ('created_at', DateRangeFilter)
    )
    list_select_related = ('room', 'position', 'division', 'department')
    list_display_links = ('full_name',)
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
    list_per_page = 100
    
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('full_name', 'birth_date', 'avatar', 'avatar_cropping', 'employment_type', 'division', 'department', 'position', 'room')
        }),
        (_('Порядок отображения'), {
            'fields': ('display_order',),
            'description': _('Укажите порядок отображения сотрудника в списке. Меньшее число = выше в списке. Если не указано, сортировка по алфавиту.')
        }),
        (_('Контакты'), {
            'fields': ('work_phone', 'mobile_phone', 'email')
        }),
        (_('Учетная запись пользователя'), {
            'fields': ('user', 'user_info'),
            'description': _('Информация о пользователе для доступа к чату. Пользователь создается автоматически при указании email.')
        }),
        (_('Дополнительно'), {
            'fields': ('notes',)
        }),
        (_('Системная информация'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'user_info')
    resource_class = ContactResource
    
    # Автозаполнение для удобства
    autocomplete_fields = ['division', 'department', 'position', 'room']
    list_display_links = ('full_name',)
    
    def user_info(self, obj):
        """Отображает информацию о связанном пользователе"""
        if obj.user:
            return format_html(
                '<div style="padding: 10px; background-color: #e8f4f8; border-radius: 5px; border-left: 4px solid #2196F3;">'
                '<strong>👤 Пользователь:</strong><br>'
                '<span style="font-size: 14px;">'
                '<strong>Username:</strong> <code style="background: white; padding: 2px 6px; border-radius: 3px;">{}</code><br>'
                '<strong>Email:</strong> <code style="background: white; padding: 2px 6px; border-radius: 3px;">{}</code><br>'
                '<strong>Активен:</strong> {}'
                '</span>'
                '</div>',
                obj.user.username,
                obj.user.email,
                '✅ Да' if obj.user.is_active else '❌ Нет'
            )
        else:
            if obj.email:
                return format_html(
                    '<div style="padding: 10px; background-color: #fff3cd; border-radius: 5px; border-left: 4px solid #ffc107;">'
                    '<strong>⚠️ Пользователь не создан</strong><br>'
                    '<span style="font-size: 12px; color: #856404;">'
                    'Email указан: <code>{}</code><br>'
                    'Пользователь будет создан автоматически при сохранении.'
                    '</span>'
                    '</div>',
                    obj.email
                )
            else:
                return format_html(
                    '<div style="padding: 10px; background-color: #f8d7da; border-radius: 5px; border-left: 4px solid #dc3545;">'
                    '<strong>❌ Пользователь не создан</strong><br>'
                    '<span style="font-size: 12px; color: #721c24;">'
                    'Для создания пользователя необходимо указать email.'
                    '</span>'
                    '</div>'
                )
    user_info.short_description = _('Информация о пользователе')
    user_info.help_text = _('Информация о связанной учетной записи пользователя для доступа к чату')
    
    def save_model(self, request, obj, form, change):
        """
        Переопределяем сохранение для вывода сообщения о создании пользователя.
        """
        # Сохраняем информацию о том, был ли email до сохранения
        if change and obj.pk:
            try:
                old_obj = Contact.objects.get(pk=obj.pk)
                old_email = old_obj.email
                old_user = old_obj.user
            except Contact.DoesNotExist:
                old_email = None
                old_user = None
        else:
            old_email = None
            old_user = None
        
        # Сохраняем объект
        super().save_model(request, obj, form, change)
        
        # Обновляем объект из БД, чтобы получить актуальную информацию о пользователе
        obj.refresh_from_db()
        
        # Проверяем, был ли создан или связан пользователь
        if obj.email and obj.user:
            # Проверяем, был ли это новый пользователь или существующий
            if not change or not old_user:
                # Новый пользователь был создан
                messages.success(
                    request,
                    format_html(
                        '✅ <strong>Пользователь создан!</strong><br>'
                        '👤 <strong>Username:</strong> <code>{}</code><br>'
                        '📧 <strong>Email:</strong> <code>{}</code><br>'
                        '🔑 <strong>Стандартный пароль:</strong> <code style="background: #fff3cd; padding: 2px 6px; border-radius: 3px; font-weight: bold;">Chat2026</code><br>'
                        '<small style="color: #856404;">⚠️ Пользователь должен сменить пароль при первом входе.</small>',
                        obj.user.username,
                        obj.user.email
                    )
                )
            elif old_email != obj.email and old_user != obj.user:
                # Email был изменен и пользователь был пересоздан или связан новый
                messages.info(
                    request,
                    format_html(
                        'ℹ️ <strong>Пользователь обновлен!</strong><br>'
                        '👤 <strong>Username:</strong> <code>{}</code><br>'
                        '📧 <strong>Email:</strong> <code>{}</code>',
                        obj.user.username,
                        obj.user.email
                    )
                )
    
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
    """Форма вакансии с подключенным CKEditor и фильтрацией управлений по департаменту."""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем управления по выбранному департаменту
        if 'department' in self.data:
            try:
                department_id = self.data.get('department')
                if department_id:
                    # Если департамент выбран - показываем управления этого департамента
                    department_id = int(department_id)
                    self.fields['division'].queryset = Division.objects.filter(
                        department_id=department_id
                    ).order_by('name_ru')
                else:
                    # Если департамент не выбран - показываем независимые управления (без департамента)
                    self.fields['division'].queryset = Division.objects.filter(
                        department__isnull=True
                    ).order_by('name_ru')
            except (ValueError, TypeError):
                # Невалидный ID департамента - показываем независимые управления
                self.fields['division'].queryset = Division.objects.filter(
                    department__isnull=True
                ).order_by('name_ru')
        elif self.instance and self.instance.pk:
            # При редактировании существующей вакансии
            if self.instance.department:
                # Показываем управления выбранного департамента
                self.fields['division'].queryset = Division.objects.filter(
                    department=self.instance.department
                ).order_by('name_ru')
            else:
                # Если департамент не выбран - показываем независимые управления
                self.fields['division'].queryset = Division.objects.filter(
                    department__isnull=True
                ).order_by('name_ru')
        else:
            # При создании новой вакансии без выбранного департамента - показываем независимые управления
            self.fields['division'].queryset = Division.objects.filter(
                department__isnull=True
            ).order_by('name_ru')


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
    list_display = ('id', 'position', 'department', 'is_active', 'display_order', 'created_at')
    list_filter = (
        'is_active',
        ('department', RelatedDropdownFilter),
        ('position', RelatedDropdownFilter),
        ('created_at', DateRangeFilter)
    )
    list_editable = ('is_active', 'display_order')
    search_fields = ('position__name_ru', 'position__name_kk', 'description_ru', 'description_kk')
    list_per_page = 50
    list_display_links = ('position',)
    list_select_related = ('position', 'department', 'division')

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('position', 'department', 'division', 'is_active')
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
    resource_class = VacancyResource

    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем метод для фильтрации управлений по департаменту."""
        form = super().get_form(request, obj, **kwargs)
        
        # Если редактируем существующую вакансию
        if obj and obj.department:
            # Показываем управления выбранного департамента
            form.base_fields['division'].queryset = Division.objects.filter(
                department=obj.department
            ).order_by('name_ru')
        else:
            # При создании новой вакансии или если департамент не выбран - показываем независимые управления
            form.base_fields['division'].queryset = Division.objects.filter(
                department__isnull=True
            ).order_by('name_ru')
        
        return form

    def get_urls(self):
        """Добавляем кастомный URL для получения управлений по департаменту."""
        urls = super().get_urls()
        custom_urls = [
            path(
                'get-divisions-by-department/',
                self.admin_site.admin_view(self.get_divisions_by_department),
                name='contacts_vacancy_get_divisions',
            ),
        ]
        return custom_urls + urls

    def get_divisions_by_department(self, request):
        """Возвращает JSON со списком управлений для выбранного департамента или независимые управления."""
        department_id = request.GET.get('department_id')
        
        if department_id:
            try:
                # Если департамент выбран - возвращаем управления этого департамента
                divisions = Division.objects.filter(
                    department_id=int(department_id)
                ).order_by('name_ru')
            except (ValueError, TypeError):
                # Невалидный ID - возвращаем независимые управления
                divisions = Division.objects.filter(
                    department__isnull=True
                ).order_by('name_ru')
        else:
            # Если департамент не выбран - возвращаем независимые управления (без департамента)
            divisions = Division.objects.filter(
                department__isnull=True
            ).order_by('name_ru')
        
        divisions_data = [
            {'id': div.id, 'name_ru': div.name_ru}
            for div in divisions
        ]
        return JsonResponse({'divisions': divisions_data})

    class Media:
        js = ('admin/js/vacancy_admin.js',)


