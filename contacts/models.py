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
