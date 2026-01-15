# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import gettext_lazy as _
from image_cropping import ImageRatioField


class Department(models.Model):
    """
    Модель для структурных подразделений/отделов.
    """
    # Название отдела на русском языке
    name_ru = models.CharField(
        max_length=300,
        verbose_name=_('Название отдела (русский)'),
        db_index=True
    )
    
    # Название отдела на казахском языке
    name_kk = models.CharField(
        max_length=300,
        verbose_name=_('Название отдела (казахский)'),
        blank=True,
        null=True
    )
    
    # Родительский отдел (для иерархии)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Родительский отдел')
    )
    
    # Описание отдела
    description = models.TextField(
        verbose_name=_('Описание'),
        blank=True,
        null=True
    )
    
    # Порядок отображения (для сортировки в списке)
    display_order = models.IntegerField(
        verbose_name=_('Порядок отображения'),
        blank=True,
        null=True,
        help_text=_('Число для указания порядка отображения отдела в списке. Меньшее число = выше в списке. Если не указано, сортировка по алфавиту.')
    )
    
    # Дата создания
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    
    # Дата обновления
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Отдел')
        verbose_name_plural = _('Отделы')
        ordering = ['display_order', 'name_ru']
        indexes = [
            models.Index(fields=['name_ru']),
        ]

    def __str__(self):
        return self.name_ru


class Position(models.Model):
    """
    Модель для должностей сотрудников.
    """
    # Название должности на русском языке
    name_ru = models.CharField(
        max_length=200,
        verbose_name=_('Название должности (русский)'),
        db_index=True
    )
    
    # Название должности на казахском языке
    name_kk = models.CharField(
        max_length=200,
        verbose_name=_('Название должности (казахский)'),
        blank=True,
        null=True
    )
    
    # Описание должности
    description = models.TextField(
        verbose_name=_('Описание'),
        blank=True,
        null=True
    )
    
    # Дата создания
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    
    # Дата обновления
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Должность')
        verbose_name_plural = _('Должности')
        ordering = ['name_ru']
        indexes = [
            models.Index(fields=['name_ru']),
        ]

    def __str__(self):
        return self.name_ru


class Room(models.Model):
    """
    Модель для кабинетов/помещений.
    """
    # Номер кабинета - основной критерий поиска
    number = models.CharField(
        max_length=20,
        verbose_name=_('Номер кабинета'),
        unique=True,
        db_index=True,
        help_text=_('Номер кабинета (например: 751, 1023)')
    )
    
    # Описание кабинета (этаж, корпус и т.д.)
    description = models.CharField(
        max_length=200,
        verbose_name=_('Описание'),
        blank=True,
        null=True,
        help_text=_('Дополнительная информация о кабинете')
    )
    
    # Этаж
    floor = models.IntegerField(
        verbose_name=_('Этаж'),
        blank=True,
        null=True
    )
    
    # Корпус/здание
    building = models.CharField(
        max_length=100,
        verbose_name=_('Корпус/Здание'),
        blank=True,
        null=True
    )
    
    # Дата создания
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    
    # Дата обновления
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Кабинет')
        verbose_name_plural = _('Кабинеты')
        ordering = ['number']
        indexes = [
            models.Index(fields=['number']),
        ]

    def __str__(self):
        return self.number


class Contact(models.Model):
    """
    Модель для хранения контактной информации сотрудников.
    Связывает сотрудника с отделом, должностью и кабинетом.
    """
    # Связь с отделом
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        verbose_name=_('Отдел'),
        db_index=True
    )
    
    # Связь с должностью
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        verbose_name=_('Должность'),
        db_index=True
    )
    
    # Связь с кабинетом
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        verbose_name=_('Кабинет'),
        db_index=True
    )
    
    # ФИО сотрудника
    full_name = models.CharField(
        max_length=200,
        verbose_name=_('ФИО'),
        db_index=True,  # Индекс для поиска по ФИО
    )
    
    # Порядок отображения (для сортировки внутри отдела)
    display_order = models.IntegerField(
        verbose_name=_('Порядок отображения'),
        blank=True,
        null=True,
        help_text=_('Число для указания порядка отображения сотрудника в списке. Меньшее число = выше в списке. Если не указано, сортировка по алфавиту.')
    )
    
    # Аватарка сотрудника (необязательное поле)
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name=_('Аватарка'),
        blank=True,
        null=True,
        help_text=_('Фото сотрудника (необязательно)')
    )
    
    # Координаты обрезки аватарки (используется ImageRatioField из django-image-cropping)
    # Формат: 'widthxheight' - например '400x400' для квадратного изображения
    avatar_cropping = ImageRatioField(
        'avatar',
        '400x400',
        verbose_name=_('Обрезка аватарки'),
        help_text=_('Выберите область для обрезки изображения. Рекомендуемый размер: 400x400 пикселей'),
        free_crop=True,  # Позволяет свободную обрезку
        size_warning=True,  # Предупреждение о размере
        adapt_rotation=False,  # Не адаптировать поворот
    )
    
    # Рабочий телефон
    work_phone = models.CharField(
        max_length=50,
        verbose_name=_('Рабочий телефон'),
        blank=True,
        null=True,
        db_index=True
    )
    
    # Мобильный телефон
    mobile_phone = models.CharField(
        max_length=50,
        verbose_name=_('Мобильный телефон'),
        blank=True,
        null=True
    )
    
    # Email (на будущее)
    email = models.EmailField(
        verbose_name=_('Email'),
        blank=True,
        null=True
    )
    
    # Примечания
    notes = models.TextField(
        verbose_name=_('Примечания'),
        blank=True,
        null=True
    )
    
    # Дата создания записи
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )
    
    # Дата обновления записи
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Контакт')
        verbose_name_plural = _('Контакты')
        ordering = ['display_order', 'full_name']
        # Составные индексы для оптимизации поиска
        indexes = [
            models.Index(fields=['room', 'full_name']),
            models.Index(fields=['department', 'position']),
            models.Index(fields=['full_name', 'work_phone']),
        ]

    def __str__(self):
        room_num = self.room.number if self.room else "N/A"
        return f"{room_num} - {self.full_name}"
    
    @property
    def room_number(self):
        """Свойство для обратной совместимости - возвращает номер кабинета"""
        return self.room.number if self.room else ""
    
    def get_cropped_avatar_url(self, size=(48, 48)):
        """
        Возвращает URL обрезанного аватара с использованием easy-thumbnails.
        Если обрезка не задана, возвращает оригинальное изображение.
        """
        if not self.avatar:
            return None
        
        try:
            from easy_thumbnails.files import get_thumbnailer
            from image_cropping import get_backend
            
            # Получаем бэкенд для обрезки
            backend = get_backend()
            
            # Если есть координаты обрезки, используем их
            if self.avatar_cropping:
                # Получаем обрезанное изображение через бэкенд
                thumbnailer = get_thumbnailer(self.avatar)
                thumbnail = thumbnailer.get_thumbnail({
                    'size': size,
                    'crop': True,
                    'box': self.avatar_cropping,  # Координаты обрезки
                })
                return thumbnail.url
            else:
                # Если обрезка не задана, возвращаем миниатюру без обрезки
                thumbnailer = get_thumbnailer(self.avatar)
                thumbnail = thumbnailer.get_thumbnail({
                    'size': size,
                    'crop': True,
                })
                return thumbnail.url
        except Exception:
            # В случае ошибки возвращаем оригинальное изображение
            return self.avatar.url

class Vacancy(models.Model):
    """
    Модель для хранения вакансий в справочнике.
    Используется для отображения вакансий на сайте.
    """
    # Должность (связь с таблицей должностей для фильтрации)
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacancies',
        verbose_name=_('Должность'),
        db_index=True,
        help_text=_('Должность для вакансии. Позволяет фильтровать вакансии по должностям.')
    )

    # Отдел в организации
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vacancies',
        verbose_name=_('Отдел'),
        db_index=True
    )

    # Описание вакансии на русском языке
    description_ru = models.TextField(
        verbose_name=_('Описание вакансии (русский)'),
        blank=True,
        null=True
    )

    # Описание вакансии на казахском языке
    description_kk = models.TextField(
        verbose_name=_('Описание вакансии (казахский)'),
        blank=True,
        null=True
    )

    # Требования и условия на русском языке (объединенное поле)
    requirements_and_conditions_ru = models.TextField(
        verbose_name=_('Требования и условия (русский)'),
        blank=True,
        null=True,
        help_text=_('Требования к кандидату и условия работы')
    )

    # Требования и условия на казахском языке (объединенное поле)
    requirements_and_conditions_kk = models.TextField(
        verbose_name=_('Требования и условия (казахский)'),
        blank=True,
        null=True,
        help_text=_('Требования к кандидату и условия работы')
    )

    # Контактная информация для отклика
    contact_info = models.CharField(
        max_length=500,
        verbose_name=_('Контактная информация'),
        blank=True,
        null=True,
        help_text=_('Email, телефон или другая контактная информация для отклика')
    )

    # Флаг активности (показывать вакансию)
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Активна'),
        help_text=_('Показывать ли вакансию в списке и на сайте')
    )

    # Порядок отображения (для сортировки в списке)
    display_order = models.IntegerField(
        verbose_name=_('Порядок отображения'),
        blank=True,
        null=True,
        help_text=_('Число для сортировки вакансий в списке. Меньшее число = выше в списке. Если не указано, сортировка по дате создания.')
    )

    # Дата создания
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата создания')
    )

    # Дата обновления
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата обновления')
    )

    class Meta:
        verbose_name = _('Вакансия')
        verbose_name_plural = _('Вакансии')
        ordering = ['display_order', '-created_at']
        indexes = [
            models.Index(fields=['position', 'is_active']),
            models.Index(fields=['department', 'is_active']),
        ]

    def __str__(self):
        if self.position:
            return self.position.name_ru
        return _('Вакансия без должности')

    def get_title(self):
        """Возвращает название должности в зависимости от языка"""
        if not self.position:
            return ''
        from django.utils import translation
        lang = translation.get_language()
        if lang == 'kk' and self.position.name_kk:
            return self.position.name_kk
        return self.position.name_ru

    def get_description(self):
        """Возвращает описание вакансии в зависимости от языка"""
        from django.utils import translation
        lang = translation.get_language()
        if lang == 'kk' and self.description_kk:
            return self.description_kk
        return self.description_ru or ''

    def get_requirements_and_conditions(self):
        """Возвращает требования и условия в зависимости от языка"""
        from django.utils import translation
        lang = translation.get_language()
        if lang == 'kk' and self.requirements_and_conditions_kk:
            return self.requirements_and_conditions_kk
        return self.requirements_and_conditions_ru or ''

    def get_requirements(self):
        """Обратная совместимость: возвращает требования и условия"""
        return self.get_requirements_and_conditions()

    def get_conditions(self):
        """Обратная совместимость: возвращает требования и условия"""
        return self.get_requirements_and_conditions()
