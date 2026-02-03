"""
Django settings for hr_guide project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Разрешенные хосты (можно указать через запятую в переменной окружения)
# Для работы по локальной сети добавляем IP адреса автоматически
ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS', '*')
if ALLOWED_HOSTS_ENV and ALLOWED_HOSTS_ENV != '*':
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',')]
else:
    # Разрешаем все хосты для работы по локальной сети
    # В production лучше указать конкретные домены/IP
    ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # 'jazzmin',  # Современная админ-панель (должна быть перед django.contrib.admin)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',  # Django Channels для WebSocket
    'rest_framework',  # Django REST Framework для API
    'contacts.apps.ContactsConfig',  # Наше приложение для контактов
    'messaging',  # Приложение для чата
    'image_cropping',  # Для обрезки изображений
    'easy_thumbnails',  # Для создания миниатюр
    'import_export',  # Для импорта и экспорта данных в админке
    'ckeditor',  # Для редактора текста
    'django_admin_listfilter_dropdown',  # Фильтры с выпадающим списком
    'rangefilter',  # Фильтр по датам
    'django_celery_results',  # Хранение результатов Celery в БД, просмотр в админке
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise для эффективного обслуживания статических файлов
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Для поддержки локализации
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'contacts.middleware.RequirePasswordChangeMiddleware',  # Проверка стандартного пароля
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hr_guide.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',  # Для локализации
                'contacts.context_processors.user_display_name',  # ФИО пользователя в шапке
                'contacts.context_processors.developer_contacts',  # Контакты разработчика для футера и страницы связи
            ],
        },
    },
]

WSGI_APPLICATION = 'hr_guide.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Настройка базы данных: PostgreSQL в Docker, SQLite локально
DATABASE_HOST = os.environ.get('DATABASE_HOST', '')
DATABASE_PORT = os.environ.get('DATABASE_PORT', '5432')
DATABASE_NAME = os.environ.get('DATABASE_NAME', '')
DATABASE_USER = os.environ.get('DATABASE_USER', '')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', '')

if DATABASE_HOST and DATABASE_NAME and DATABASE_USER:
    # Используем PostgreSQL, если указаны переменные окружения
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DATABASE_NAME,
            'USER': DATABASE_USER,
            'PASSWORD': DATABASE_PASSWORD,
            'HOST': DATABASE_HOST,
            'PORT': DATABASE_PORT,
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    # Используем SQLite по умолчанию
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = os.environ.get('LANGUAGE_CODE', 'ru')

TIME_ZONE = os.environ.get('TIME_ZONE', 'Asia/Almaty')

USE_I18N = os.environ.get('USE_I18N', 'True') == 'True'

USE_TZ = os.environ.get('USE_TZ', 'True') == 'True'

# Поддержка казахского языка
LANGUAGES = [
    ('ru', 'Русский'),
    ('kk', 'Қазақша'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# 1. Папка, куда Django БУДЕТ СОБИРАТЬ все файлы (ваша итоговая папка)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 2. Папки, из которых Django БЕРЕТ файлы при сборке (ваша папка с исходниками)
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# 3. URL для доступа к файлам
STATIC_URL = '/static/'
# Вместо CompressedManifestStaticFilesStorage
# Вместо CompressedManifestStaticFilesStorage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Media files (загруженные пользователями файлы)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Настройки WhiteNoise для эффективного обслуживания статических файлов
# WhiteNoise обслуживает статику напрямую из Django, что хорошо для работы по локальной сети
# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",  # Сжатие и кэширование статики
#     },
# }

# Дополнительные настройки WhiteNoise (опционально, можно настроить кэширование и сжатие)
WHITENOISE_USE_FINDERS = True  # Позволяет обслуживать статику из STATICFILES_DIRS в режиме разработки
WHITENOISE_AUTOREFRESH = DEBUG  # Автообновление при изменениях в режиме разработки
WHITENOISE_MAX_AGE = 31536000  # 1 год в секундах

# Настройки для easy-thumbnails
THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_ALIASES = {
    '': {
        'avatar_small': {'size': (50, 50), 'crop': True},
        'avatar_medium': {'size': (100, 100), 'crop': True},
        'avatar_large': {'size': (200, 200), 'crop': True},
    },
}

# Добавляем процессор обрезки для easy-thumbnails
from easy_thumbnails.conf import Settings as thumbnail_settings
THUMBNAIL_PROCESSORS = (
    'image_cropping.thumbnail_processors.crop_corners',
) + thumbnail_settings.THUMBNAIL_PROCESSORS

# Настройки для image-cropping
IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_BACKEND = 'image_cropping.backends.easy_thumbs.EasyThumbnailsBackend'
IMAGE_CROPPING_BACKEND_PARAMS = {}

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки авторизации
# Авторизация нужна только для админ-панели, основной функционал доступен всем
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/search/'
LOGOUT_REDIRECT_URL = '/'

# Настройки для CKEditor
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
        'language': 'ru',
    },
}

# Настройки для django-import-export
# Настройки для django-import-export
# Для поддержки XLSX требуется библиотека openpyxl (уже добавлена в requirements.txt)
# django-import-export автоматически определит доступные форматы при установке openpyxl
IMPORT_EXPORT_USE_TRANSACTIONS = True  # Использовать транзакции при импорте
IMPORT_EXPORT_SKIP_ADMIN_LOG = False  # Логировать импорт в админке
IMPORT_EXPORT_IMPORT_PERMISSION_CODE = 'change'  # Права доступа для импорта
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = 'view'  # Права доступа для экспорта


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

# Настройки Django Channels для WebSocket
ASGI_APPLICATION = 'hr_guide.asgi.application'

# Настройки Channels
# Используем Redis если доступен, иначе InMemoryChannelLayer для локальной разработки
# В Docker используем имя сервиса 'redis', локально - 'localhost'
REDIS_HOST = os.environ.get('REDIS_HOST', os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0').split('://')[1].split(':')[0] if '://' in os.environ.get('CELERY_BROKER_URL', '') else 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Если CELERY_BROKER_URL задан, извлекаем хост оттуда
if 'CELERY_BROKER_URL' in os.environ:
    broker_url = os.environ['CELERY_BROKER_URL']
    if '://' in broker_url:
        try:
            parts = broker_url.split('://')[1].split(':')
            REDIS_HOST = parts[0] if parts[0] else 'localhost'
            if len(parts) > 1:
                REDIS_PORT = int(parts[1].split('/')[0])
        except (ValueError, IndexError):
            pass

try:
    import redis
    # Проверяем доступность Redis
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_connect_timeout=2)
    r.ping()
    # Redis доступен - используем его
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(REDIS_HOST, REDIS_PORT)],
            },
        },
    }
except (ImportError, redis.ConnectionError, redis.TimeoutError, Exception) as e:
    # Redis недоступен - используем InMemoryChannelLayer
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Redis недоступен ({REDIS_HOST}:{REDIS_PORT}), используется InMemoryChannelLayer: {e}")
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# Настройки Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Настройки Celery
# Используем переменные окружения или значения по умолчанию
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
# Результаты в БД — просмотр в админке (Django Celery Results). Redis — только брокер очереди.
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'django_celery_results.backends:DatabaseBackend')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Контакты разработчика для страницы «Связь с разработчиком»
# Задаются через переменные окружения: DEVELOPER_EMAIL, DEVELOPER_TELEGRAM (username без @), DEVELOPER_NAME (опционально)
DEVELOPER_EMAIL = os.environ.get('DEVELOPER_EMAIL', '')
DEVELOPER_TELEGRAM = (os.environ.get('DEVELOPER_TELEGRAM', '') or '').lstrip('@').strip()
DEVELOPER_NAME = os.environ.get('DEVELOPER_NAME', '')

# Расписание для Celery Beat (периодические задачи)
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    'delete-old-chat-files': {
        'task': 'messaging.tasks.delete_old_files',
        'schedule': crontab(hour=2, minute=0),  # Каждый день в 2:00 ночи
    },
}

# Период хранения файлов в чате (в днях)
CHAT_FILE_RETENTION_DAYS = 30

# Настройки аутентификации
# Поддержка входа по email или username
AUTHENTICATION_BACKENDS = [
    'contacts.backends.EmailBackend',  # Кастомный backend для входа по email
    'django.contrib.auth.backends.ModelBackend',  # Стандартный backend Django
]
