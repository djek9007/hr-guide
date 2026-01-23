#!/bin/sh
# или
#!/bin/bash
set -e

echo "Ожидание подключения к базе данных..."

# Ожидаем, пока PostgreSQL будет готов к подключениям
until python -c "
import sys
import psycopg2
try:
    conn = psycopg2.connect(
        host='${DATABASE_HOST:-host.docker.internal}',
        port='${DATABASE_PORT:-5432}',
        database='${DATABASE_NAME:-hr-guide}',
        user='${DATABASE_USER:-admin}',
        password='${DATABASE_PASSWORD:-Postgres9007}'
    )
    conn.close()
    sys.exit(0)
except psycopg2.OperationalError:
    sys.exit(1)
"; do
  echo "База данных недоступна - ждем..."
  sleep 1
done

echo "База данных готова!"

# Ожидаем Redis (опционально, не критично для старта)
echo "Проверка Redis..."
python -c "
import sys
try:
    import redis
    r = redis.Redis(host='${REDIS_HOST:-redis}', port=${REDIS_PORT:-6379}, socket_connect_timeout=2)
    r.ping()
    print('Redis доступен')
except Exception:
    print('Redis недоступен, будет использован InMemoryChannelLayer')
" || echo "Redis недоступен, будет использован InMemoryChannelLayer"

# Применяем миграции
echo "Применение миграций..."
python manage.py migrate --noinput

# Собираем статические файлы
# echo "Сборка статических файлов..."
# python manage.py collectstatic 
#python manage.py collectstatic --noinput --clear

# Создаем суперпользователя, если его нет (опционально)
echo "Проверка суперпользователя..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Суперпользователь создан: admin/admin')
else:
    print('Суперпользователь уже существует')
EOF

echo "Запуск сервера..."
exec "$@"
