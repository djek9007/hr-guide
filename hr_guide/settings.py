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
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',') if os.environ.get('ALLOWED_HOSTS') else ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin',  # Современная админ-панель (должна быть перед django.contrib.admin)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'contacts',  # Наше приложение для контактов
    'image_cropping',  # Для обрезки изображений
    'easy_thumbnails',  # Для создания миниатюр
    'import_export',  # Для импорта и экспорта данных в админке
    'ckeditor',  # Для редактора текста
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Для поддержки локализации
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
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
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }
else:
    # Используем SQLite для локальной разработки
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

STATIC_URL = os.environ.get('STATIC_URL', 'static/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = Path(os.environ.get('STATIC_ROOT', str(BASE_DIR / 'staticfiles'))) if os.environ.get('STATIC_ROOT') else BASE_DIR / 'staticfiles'

# Media files (загруженные пользователями файлы)
MEDIA_URL = os.environ.get('MEDIA_URL', '/media/')
MEDIA_ROOT = Path(os.environ.get('MEDIA_ROOT', str(BASE_DIR / 'media'))) if os.environ.get('MEDIA_ROOT') else BASE_DIR / 'media'

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

# Настройки Jazzmin (современная админ-панель)
JAZZMIN_SETTINGS = {
    "site_title": "Телефонный справочник",
    "site_header": "Телефонный справочник",
    "site_brand": "HR Guide",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "welcome_sign": "Добро пожаловать в админ-панель",
    "copyright": "HR Guide",
    "search_model": ["contacts.Contact", "contacts.Department", "contacts.Vacancy"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Главная", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Сайт", "url": "/", "new_window": True},
    ],
    "usermenu_links": [
        {"name": "Сайт", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["contacts", "contacts.Department", "contacts.Position", "contacts.Room", "contacts.Contact", "contacts.Vacancy"],
    "custom_links": {},
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "contacts.Department": "fas fa-building",
        "contacts.Position": "fas fa-briefcase",
        "contacts.Room": "fas fa-door-open",
        "contacts.Contact": "fas fa-address-card",
        "contacts.Vacancy": "fas fa-briefcase",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": False,
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"contacts.contact": "collapsible"},
    "language_chooser": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

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
# Включаем поддержку форматов XLSX, XLS, CSV, JSON, YAML, HTML, TSV
IMPORT_EXPORT_FORMATS = {
    'xlsx': 'xlsx',
    'xls': 'xls',
    'csv': 'csv',
    'json': 'json',
    'yaml': 'yaml',
    'html': 'html',
    'tsv': 'tsv',
}
