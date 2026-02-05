# Документ проектирования: Система объявлений

## Обзор

Система объявлений представляет собой Django-приложение для управления двуязычными объявлениями (казахский и русский языки) в HR-системе. Система обеспечивает публичный доступ к просмотру объявлений без авторизации, при этом административные функции (создание, редактирование, удаление) доступны только авторизованным администраторам.

Ключевые особенности:
- Двуязычный интерфейс (казахский и русский)
- Публичный доступ к просмотру объявлений
- Rich text редактирование с использованием django-ckeditor
- Пагинация списка объявлений (20 записей на страницу)
- Счетчик новых объявлений в меню навигации
- Административная панель Django для управления объявлениями

## Архитектура

Система следует архитектуре Django MVT (Model-View-Template) и интегрируется с существующей HR-системой.

### Компоненты высокого уровня

```
┌─────────────────────────────────────────────────────────┐
│                    Веб-интерфейс                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Публичный    │  │ Админ панель │  │ Меню с       │  │
│  │ список       │  │ Django       │  │ счетчиком    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Слой представлений                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ ListView     │  │ DetailView   │  │ Admin Views  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                    Слой моделей                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Модель Announcement                  │   │
│  │  - title_kk, title_ru                            │   │
│  │  - content_kk, content_ru (RichTextField)        │   │
│  │  - created_at, created_by                        │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  База данных PostgreSQL                  │
└─────────────────────────────────────────────────────────┘
```

### Интеграция с существующей системой

Система объявлений интегрируется с:
- **Django Auth**: Использует встроенную систему аутентификации для проверки прав администраторов
- **Contact модель**: Связывается через User модель для идентификации создателя объявления
- **Система навигации**: Добавляет пункт меню со счетчиком новых объявлений
- **Система локализации**: Использует механизм переключения языков Django

## Компоненты и интерфейсы

### 1. Модель данных: Announcement

```python
from django.db import models
from django.contrib.auth.models import User
from ckeditor.fields import RichTextField
from django.utils import timezone

class Announcement(models.Model):
    # Заголовки на двух языках
    title_kk = models.CharField(max_length=255, verbose_name="Заголовок (каз)")
    title_ru = models.CharField(max_length=255, verbose_name="Заголовок (рус)")
    
    # Содержимое с rich text форматированием
    content_kk = RichTextField(verbose_name="Содержимое (каз)")
    content_ru = RichTextField(verbose_name="Содержимое (рус)")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Создатель")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
    
    def __str__(self):
        return self.title_ru
    
    def is_new(self):
        """Проверяет, является ли объявление новым (создано сегодня)"""
        return self.created_at.date() == timezone.now().date()
```

### 2. Представления (Views)

#### AnnouncementListView
Публичное представление для отображения списка объявлений с пагинацией.

```python
from django.views.generic import ListView
from django.core.paginator import Paginator

class AnnouncementListView(ListView):
    model = Announcement
    template_name = 'announcements/list.html'
    context_object_name = 'announcements'
    paginate_by = 20
    
    def get_queryset(self):
        return Announcement.objects.all().order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_language'] = self.request.LANGUAGE_CODE
        return context
```

#### AnnouncementDetailView
Публичное представление для отображения детальной информации об объявлении.

```python
from django.views.generic import DetailView

class AnnouncementDetailView(DetailView):
    model = Announcement
    template_name = 'announcements/detail.html'
    context_object_name = 'announcement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_language'] = self.request.LANGUAGE_CODE
        return context
```

### 3. Административная панель

```python
from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title_ru', 'title_kk', 'created_at', 'created_by', 'is_new']
    list_filter = ['created_at']
    search_fields = ['title_ru', 'title_kk', 'content_ru', 'content_kk']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Русский язык', {
            'fields': ('title_ru', 'content_ru')
        }),
        ('Қазақ тілі', {
            'fields': ('title_kk', 'content_kk')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'created_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Если создается новый объект
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def is_new(self, obj):
        return obj.is_new()
    is_new.boolean = True
    is_new.short_description = 'Новое'
```

### 4. Context Processor для счетчика

```python
from django.utils import timezone
from .models import Announcement

def new_announcements_count(request):
    """
    Context processor для отображения количества новых объявлений в меню
    """
    today = timezone.now().date()
    count = Announcement.objects.filter(created_at__date=today).count()
    return {
        'new_announcements_count': count if count > 0 else None
    }
```

### 5. URL конфигурация

```python
from django.urls import path
from .views import AnnouncementListView, AnnouncementDetailView

app_name = 'announcements'

urlpatterns = [
    path('', AnnouncementListView.as_view(), name='list'),
    path('<int:pk>/', AnnouncementDetailView.as_view(), name='detail'),
]
```

## Модели данных

### Схема базы данных

```
announcements_announcement
├── id (PK, AutoField)
├── title_kk (CharField, max_length=255, NOT NULL)
├── title_ru (CharField, max_length=255, NOT NULL)
├── content_kk (TextField, NOT NULL)
├── content_ru (TextField, NOT NULL)
├── created_at (DateTimeField, auto_now_add=True)
└── created_by_id (FK -> auth_user.id, ON DELETE CASCADE)

Индексы:
- PRIMARY KEY (id)
- INDEX (created_at) - для сортировки и фильтрации по дате
- FOREIGN KEY (created_by_id) REFERENCES auth_user(id)
```

### Валидация данных

Валидация выполняется на уровне модели Django:

1. **Обязательные поля**: title_kk, title_ru, content_kk, content_ru - все помечены как NOT NULL
2. **Длина заголовков**: Ограничена 255 символами
3. **Санитизация HTML**: django-ckeditor автоматически санитизирует HTML для предотвращения XSS
4. **Автор объявления**: Автоматически устанавливается при создании через админ-панель

## Свойства корректности

*Свойство - это характеристика или поведение, которое должно выполняться во всех допустимых выполнениях системы - по сути, формальное утверждение о том, что должна делать система. Свойства служат мостом между человекочитаемыми спецификациями и машинно-проверяемыми гарантиями корректности.*


### Свойство 1: Автоматическая установка временной метки при создании

*For any* новое объявление, при создании должна автоматически устанавливаться временная метка created_at, близкая к текущему времени (в пределах нескольких секунд).

**Validates: Requirements 1.1**

### Свойство 2: Валидация обязательных полей

*For any* попытка создания или обновления объявления с пустым значением в любом из обязательных полей (title_kk, title_ru, content_kk, content_ru), операция должна быть отклонена с ошибкой валидации.

**Validates: Requirements 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4**

### Свойство 3: Сохранение HTML-форматирования (Round-trip)

*For any* объявление с HTML-форматированием в полях содержимого, после сохранения в базу данных и последующего чтения, форматирование должно быть сохранено (безопасные HTML-теги остаются неизменными).

**Validates: Requirements 1.6**

### Свойство 4: Обновление полей объявления

*For any* существующее объявление и новые значения полей, после обновления объявления, все измененные поля должны содержать новые значения.

**Validates: Requirements 2.1**

### Свойство 5: Инвариант временной метки создания

*For any* объявление, временная метка created_at должна оставаться неизменной при любых операциях обновления объявления.

**Validates: Requirements 2.2**

### Свойство 6: Полное удаление объявления

*For any* объявление, после операции удаления, попытка получить это объявление из базы данных должна вызвать исключение (объект не существует).

**Validates: Requirements 3.1**

### Свойство 7: Сортировка объявлений по дате

*For any* список объявлений, возвращаемый системой, объявления должны быть отсортированы по полю created_at в порядке убывания (новые первыми).

**Validates: Requirements 4.3**

### Свойство 8: Пагинация - размер страницы

*For any* запрос первой страницы списка объявлений, если общее количество объявлений больше 20, то должно быть возвращено ровно 20 объявлений.

**Validates: Requirements 4.4**

### Свойство 9: Пагинация - наличие навигации

*For any* запрос списка объявлений, если общее количество объявлений превышает 20, то в ответе должна присутствовать информация о пагинации (номер текущей страницы, общее количество страниц, ссылки на следующую/предыдущую страницы).

**Validates: Requirements 4.5**

### Свойство 10: Определение нового объявления

*For any* объявление, метод is_new() должен возвращать True тогда и только тогда, когда дата создания объявления (created_at.date()) равна текущей дате.

**Validates: Requirements 5.2**

### Свойство 11: Счетчик новых объявлений

*For any* момент времени, количество новых объявлений в счетчике должно быть равно количеству объявлений, созданных в текущий день.

**Validates: Requirements 5.1**

### Свойство 12: Отображение контента на выбранном языке

*For any* объявление и выбранный язык (казахский или русский), отображаемый контент должен содержать заголовок и содержимое на соответствующем языке (title_kk и content_kk для казахского, title_ru и content_ru для русского).

**Validates: Requirements 6.1, 6.2, 4.2**

### Свойство 13: Сохранение выбора языка

*For any* посетитель, после выбора языка интерфейса, последующие запросы в рамках той же сессии должны использовать выбранный язык.

**Validates: Requirements 6.3**

### Свойство 14: Валидация связи с пользователем

*For any* попытка создания объявления с несуществующим или невалидным идентификатором пользователя в поле created_by, операция должна быть отклонена с ошибкой целостности данных.

**Validates: Requirements 7.5**

### Свойство 15: Проверка прав администратора

*For any* пользователь без административных прав, попытка создания, редактирования или удаления объявления через административную панель должна быть отклонена с ошибкой доступа.

**Validates: Requirements 8.2**

### Свойство 16: Санитизация вредоносного HTML

*For any* попытка сохранения объявления с потенциально вредоносным HTML-кодом (например, <script> теги), система должна санитизировать контент, удаляя опасные элементы, но сохраняя безопасное форматирование.

**Validates: Requirements 9.2**

## Обработка ошибок

### Ошибки валидации

1. **Пустые обязательные поля**: Django автоматически генерирует ValidationError при попытке сохранить модель с пустыми обязательными полями
2. **Некорректный HTML**: django-ckeditor санитизирует HTML на стороне клиента и сервера
3. **Несуществующий пользователь**: Django генерирует IntegrityError при нарушении внешнего ключа

### Ошибки доступа

1. **Неавторизованный доступ к админ-панели**: Django перенаправляет на страницу входа
2. **Недостаточно прав**: Django возвращает HTTP 403 Forbidden

### Ошибки базы данных

1. **Объект не найден**: Django генерирует DoesNotExist exception
2. **Нарушение целостности**: Django генерирует IntegrityError

Все исключения должны быть обработаны на уровне представлений с возвратом понятных сообщений об ошибках пользователю.

## Стратегия тестирования

### Двойной подход к тестированию

Система использует комбинацию unit-тестов и property-based тестов для обеспечения комплексного покрытия:

- **Unit-тесты**: Проверяют конкретные примеры, граничные случаи и условия ошибок
- **Property-тесты**: Проверяют универсальные свойства на множестве сгенерированных входных данных

### Unit-тестирование

Unit-тесты фокусируются на:
- Конкретных примерах корректного поведения (создание объявления с валидными данными)
- Граничных случаях (пустой список объявлений, ровно 20 объявлений, 21 объявление)
- Интеграции компонентов (взаимодействие модели с админ-панелью)
- Специфических условиях ошибок (попытка доступа без прав)

### Property-Based тестирование

Для property-based тестирования используется библиотека **Hypothesis** (стандарт для Python/Django).

**Конфигурация**:
- Минимум 100 итераций на каждый property-тест
- Каждый тест должен ссылаться на соответствующее свойство из документа проектирования
- Формат тега: **Feature: announcement-system, Property {number}: {property_text}**

**Генераторы данных**:
```python
from hypothesis import strategies as st
from hypothesis.extra.django import from_model

# Генератор для объявлений
announcements = from_model(
    Announcement,
    title_kk=st.text(min_size=1, max_size=255),
    title_ru=st.text(min_size=1, max_size=255),
    content_kk=st.text(min_size=1),
    content_ru=st.text(min_size=1),
)

# Генератор для HTML-контента
safe_html = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1
).map(lambda s: f"<p>{s}</p>")

# Генератор для дат
dates = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31)
)
```

**Примеры property-тестов**:

```python
from hypothesis import given, settings
from hypothesis.extra.django import TestCase

class AnnouncementPropertyTests(TestCase):
    
    @given(announcements)
    @settings(max_examples=100)
    def test_property_1_created_at_set_on_creation(self, announcement):
        """
        Feature: announcement-system, Property 1: Автоматическая установка временной метки при создании
        """
        before = timezone.now()
        announcement.save()
        after = timezone.now()
        
        assert announcement.created_at is not None
        assert before <= announcement.created_at <= after
    
    @given(st.text(max_size=0))
    @settings(max_examples=100)
    def test_property_2_empty_fields_rejected(self, empty_value):
        """
        Feature: announcement-system, Property 2: Валидация обязательных полей
        """
        with pytest.raises(ValidationError):
            Announcement.objects.create(
                title_kk=empty_value,
                title_ru="Test",
                content_kk="Test",
                content_ru="Test",
                created_by=self.user
            )
```

### Тестовое покрытие

Целевое покрытие кода: минимум 80%
- Модели: 100% (критически важны)
- Представления: 90%
- Административная панель: 80%
- Утилиты и хелперы: 90%

### Интеграционное тестирование

Интеграционные тесты проверяют:
- Полный цикл создания, чтения, обновления и удаления объявлений через веб-интерфейс
- Корректную работу пагинации с реальными данными
- Переключение языков и отображение контента
- Работу счетчика новых объявлений в навигации
- Интеграцию с django-ckeditor

### Тестирование безопасности

Специальные тесты для проверки:
- XSS-защиты (попытки внедрения скриптов)
- CSRF-защиты для форм администратора
- Проверки прав доступа
- SQL-инъекций (через ORM Django)
