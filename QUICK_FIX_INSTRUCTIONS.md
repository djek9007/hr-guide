# Быстрое исправление ошибки

## Проблема
Ошибка `Cannot resolve keyword 'created_at' into field` возникает потому что код обновлен, но миграция еще не применена к базе данных.

## Решение

### Вариант 1: Применить миграцию (рекомендуется)

Если вы используете Docker:

```bash
docker-compose exec web python manage.py migrate announcements
```

Если запускаете локально:

```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Примените миграцию
python manage.py migrate announcements
```

### Вариант 2: Пересоздать миграцию (если возникли проблемы)

Если миграция не применяется корректно:

```bash
# Удалите файл миграции
rm announcements/migrations/0002_rename_fields_to_published_date_and_author.py

# Создайте новую миграцию
python manage.py makemigrations announcements

# Примените миграцию
python manage.py migrate announcements
```

## Что изменилось

1. **`created_at` → `published_date`**
   - Теперь администратор вручную указывает дату публикации
   - Поле больше не заполняется автоматически

2. **`created_by` → `author`**
   - Автор автоматически устанавливается при создании
   - Поле доступно только для чтения

3. **Обновлены все файлы:**
   - ✅ models.py
   - ✅ admin.py
   - ✅ views.py
   - ✅ context_processors.py
   - ✅ templates (list.html, detail.html)
   - ✅ tests (test_models.py, test_properties.py, test_ckeditor_config.py)

## После применения миграции

Перезапустите сервер:

```bash
# Docker
docker-compose restart web

# Локально
# Остановите сервер (Ctrl+C) и запустите снова
python manage.py runserver
```

Теперь админка должна работать корректно!
