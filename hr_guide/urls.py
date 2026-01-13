"""
URL configuration for hr_guide project.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language
from contacts import views as contacts_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Авторизация
    path('login/', contacts_views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Переключение языка
    path('i18n/setlang/', set_language, name='set_language'),
    
    # Приложение contacts
    path('', include('contacts.urls')),  # Подключаем URLs приложения contacts
]

# Для разработки - обслуживание статических и медиа файлов
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
