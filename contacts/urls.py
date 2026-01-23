from django.urls import path
from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.list_contacts, name='list'),  # Главная страница - список всех контактов
    path('list/', views.list_contacts, name='list'),  # Список всех контактов
    path('search/', views.search_contacts, name='search'),  # Страница поиска
    path('vacancies/', views.list_vacancies, name='vacancies'),  # Страница вакансий
    path('vacancies/<int:pk>/', views.vacancy_detail, name='vacancy_detail'),  # Детальная страница вакансии
]
