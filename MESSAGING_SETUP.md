# Настройка системы чата

## 🐳 Запуск в Docker (рекомендуется)

Проект настроен для работы в Docker с полной поддержкой всех компонентов.

### Быстрый старт:

1. Убедитесь, что у вас установлены Docker и Docker Compose

2. Запустите все сервисы:
   ```bash
   docker-compose up -d
   ```

3. Применение миграций (выполняется автоматически при старте):
   ```bash
   docker-compose exec hr-guide-web python manage.py migrate
   ```

4. Создание суперпользователя (если нужно):
   ```bash
   docker-compose exec hr-guide-web python manage.py createsuperuser
   ```

5. Откройте в браузере: http://localhost:8880

### Структура сервисов в Docker:

- **hr-guide-web** - Django приложение с ASGI (daphne) для поддержки WebSocket
- **db-hr** - PostgreSQL база данных
- **redis** - Redis для Celery и Channels
- **celery-worker** - Celery worker для фоновых задач
- **celery-beat** - Celery beat для периодических задач (автоудаление файлов)

### Полезные команды:

```bash
# Просмотр логов
docker-compose logs -f hr-guide-web
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat

# Остановка всех сервисов
docker-compose down

# Пересборка образов
docker-compose build --no-cache

# Выполнение команд в контейнере
docker-compose exec hr-guide-web python manage.py shell
docker-compose exec hr-guide-web python manage.py migrate
```

## 💻 Локальная разработка (без Docker)

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка базы данных

1. Создайте миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Настройка Redis (для Celery и Channels)

Для локальной разработки можно использовать InMemoryChannelLayer (автоматически используется если Redis недоступен).

Для полной функциональности рекомендуется использовать Redis:

1. Установите Redis:
   - Windows: скачайте с https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`

2. Запустите Redis:
   ```bash
   redis-server
   ```

Настройки автоматически определят доступность Redis и переключатся на него.

### Настройка Celery

#### Для локальной разработки (без Redis):

Celery будет работать, но периодические задачи (автоудаление файлов) нужно запускать вручную:

```bash
python manage.py shell
>>> from messaging.tasks import delete_old_files
>>> delete_old_files()
```

#### Для production (с Redis):

1. Запустите Celery worker:
   ```bash
   celery -A hr_guide worker --loglevel=info
   ```

2. Запустите Celery Beat (для периодических задач):
   ```bash
   celery -A hr_guide beat --loglevel=info
   ```

### Запуск сервера

#### Обычный режим (HTTP, без WebSocket):
```bash
python manage.py runserver
```

#### С поддержкой WebSocket (ASGI):
```bash
# Используйте daphne
daphne -b 0.0.0.0 -p 8000 hr_guide.asgi:application
```

Или с uvicorn:
```bash
uvicorn hr_guide.asgi:application --host 0.0.0.0 --port 8000
```

## Использование

1. Войдите в систему через `/login/`
2. Перейдите в чат через `/chat/`
3. Создайте новый чат, выбрав сотрудника из списка
4. Отправляйте сообщения и файлы

## API Endpoints

- `GET /api/chats/` - Список чатов текущего пользователя
- `GET /api/chats/get_or_create/?user_id=123` - Получить или создать чат с пользователем
- `POST /api/chats/{id}/mark_read/` - Отметить чат как прочитанный
- `GET /api/messages/?chat_id=123` - Сообщения чата
- `POST /api/messages/` - Создать сообщение (можно с файлами)
- `GET /api/users/` - Список пользователей (сотрудников)
- `GET /api/users/me/` - Текущий пользователь

## WebSocket

WebSocket подключение: `ws://localhost:8000/ws/chat/`

События:
- `chat_message` - Новое сообщение
- `typing` - Индикатор печати

## Автоудаление файлов

Файлы автоматически удаляются через 30 дней после загрузки.

Задача запускается каждый день в 2:00 ночи через Celery Beat.

Для ручного запуска:
```bash
python manage.py shell
>>> from messaging.tasks import delete_old_files
>>> delete_old_files()
```

## Примечания

- Все скрипты и стили включены локально (Alpine.js, Tailwind CSS, FontAwesome)
- Для работы чата требуется авторизация
- Файлы сохраняются в `media/chat_files/`
- Максимальный размер файла настраивается в Django settings (по умолчанию 2.5 МБ)
