# 🐳 Настройка проекта в Docker

## Быстрый старт

1. **Запустите все сервисы:**
   ```bash
   docker-compose up -d
   ```

2. **Проверьте статус сервисов:**
   ```bash
   docker-compose ps
   ```

3. **Откройте в браузере:**
   - Приложение: http://localhost:8880
   - Админ-панель: http://localhost:8880/admin
   - Логин: `admin` / Пароль: `admin` (создается автоматически)

## Структура сервисов

### hr-guide-web
- Django приложение с ASGI (daphne)
- Поддержка WebSocket для real-time чата
- Порт: 8880

### db-hr
- PostgreSQL база данных
- Версия: 17.2

### redis
- Redis для Celery и Channels
- Порт: 6379

### celery-worker
- Celery worker для фоновых задач
- Обрабатывает задачи удаления файлов

### celery-beat
- Celery beat для периодических задач
- Автоматически удаляет файлы через 30 дней (запуск в 2:00 ночи)

## Полезные команды

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f hr-guide-web
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
docker-compose logs -f redis
```

### Выполнение команд в контейнере
```bash
# Django shell
docker-compose exec hr-guide-web python manage.py shell

# Миграции
docker-compose exec hr-guide-web python manage.py migrate

# Создание суперпользователя
docker-compose exec hr-guide-web python manage.py createsuperuser

# Сборка статических файлов
docker-compose exec hr-guide-web python manage.py collectstatic --noinput
```

### Перезапуск сервисов
```bash
# Все сервисы
docker-compose restart

# Конкретный сервис
docker-compose restart hr-guide-web
docker-compose restart celery-worker
```

### Остановка и удаление
```bash
# Остановка
docker-compose stop

# Остановка и удаление контейнеров
docker-compose down

# Остановка и удаление контейнеров + volumes (удалит данные БД!)
docker-compose down -v
```

### Пересборка образов
```bash
# Пересборка без кэша
docker-compose build --no-cache

# Пересборка и перезапуск
docker-compose up -d --build
```

## Переменные окружения

Основные настройки в `.env` файле:

```env
# База данных
DATABASE_HOST=db-hr
DATABASE_PORT=5432
DATABASE_NAME=hr-guide
DATABASE_USER=admin
DATABASE_PASSWORD=Postgres9007

# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=*

# Redis (автоматически настраивается в docker-compose.yml)
REDIS_HOST=redis
REDIS_PORT=6379
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## Решение проблем

### Проблема: Сервис не запускается
```bash
# Проверьте логи
docker-compose logs hr-guide-web

# Проверьте статус
docker-compose ps
```

### Проблема: База данных недоступна
```bash
# Проверьте, запущен ли контейнер БД
docker-compose ps db-hr

# Перезапустите БД
docker-compose restart db-hr
```

### Проблема: Redis недоступен
```bash
# Проверьте логи Redis
docker-compose logs redis

# Перезапустите Redis
docker-compose restart redis
```

### Проблема: WebSocket не работает
1. Убедитесь, что используется ASGI сервер (daphne)
2. Проверьте, что Redis запущен
3. Проверьте логи: `docker-compose logs hr-guide-web`

### Проблема: Celery задачи не выполняются
```bash
# Проверьте логи worker
docker-compose logs celery-worker

# Проверьте логи beat
docker-compose logs celery-beat

# Перезапустите сервисы
docker-compose restart celery-worker celery-beat
```

## Обновление проекта

1. **Остановите контейнеры:**
   ```bash
   docker-compose down
   ```

2. **Обновите код:**
   ```bash
   git pull  # или другой способ обновления
   ```

3. **Пересоберите и запустите:**
   ```bash
   docker-compose up -d --build
   ```

4. **Примените миграции:**
   ```bash
   docker-compose exec hr-guide-web python manage.py migrate
   ```

## Production настройки

Для production рекомендуется:

1. Изменить `DEBUG=False` в `.env`
2. Установить надежный `SECRET_KEY`
3. Настроить `ALLOWED_HOSTS` с конкретными доменами
4. Использовать внешний PostgreSQL (если нужно)
5. Настроить резервное копирование БД
6. Настроить мониторинг (логи, метрики)
7. Использовать reverse proxy (nginx) перед Django

## Резервное копирование

### База данных
```bash
# Создание бэкапа
docker-compose exec db-hr pg_dump -U admin hr-guide > backup_$(date +%Y%m%d).sql

# Восстановление
docker-compose exec -T db-hr psql -U admin hr-guide < backup_20260123.sql
```

### Медиа файлы
```bash
# Копирование медиа файлов
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```
