from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.list_contacts, name='list'),  # Главная страница - список всех контактов
    path('list/', views.list_contacts, name='list'),  # Список всех контактов
    path('search/', views.search_contacts, name='search'),  # Страница поиска
]
