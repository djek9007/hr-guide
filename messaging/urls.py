# -*- coding: utf-8 -*-
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.chat_view, name='chat'),
]
