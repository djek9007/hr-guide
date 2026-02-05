"""
URL configuration for announcements app.
"""
from django.urls import path
from .views import AnnouncementListView, AnnouncementDetailView

app_name = 'announcements'

urlpatterns = [
    path('', AnnouncementListView.as_view(), name='list'),
    path('<int:pk>/', AnnouncementDetailView.as_view(), name='detail'),
]
