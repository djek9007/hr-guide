# -*- coding: utf-8 -*-
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.db.models import Q, Max
from .models import Chat, Message, FileAttachment
from .serializers import ChatSerializer, MessageSerializer, MessageCreateSerializer, UserSerializer, FileAttachmentSerializer
from contacts.models import Contact
from django.utils import timezone
from datetime import timedelta


class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с чатами.
    """
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает чаты текущего пользователя"""
        user = self.request.user
        return Chat.objects.filter(
            Q(participant1=user) | Q(participant2=user),
            is_active=True
        ).annotate(
            last_msg_time=Max('messages__created_at')
        ).order_by('-last_msg_time', '-created_at')
    
    def get_serializer_context(self):
        """Добавляет request в контекст сериализатора"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def get_or_create(self, request):
        """
        Получает существующий чат или создает новый с указанным пользователем.
        GET /api/chats/get_or_create/?user_id=123
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if other_user == request.user:
            return Response({'error': 'Cannot create chat with yourself'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ищем существующий чат
        chat = Chat.objects.filter(
            Q(participant1=request.user, participant2=other_user) |
            Q(participant1=other_user, participant2=request.user)
        ).first()
        
        if not chat:
            # Создаем новый чат
            chat = Chat.objects.create(
                participant1=request.user,
                participant2=other_user
            )
        
        serializer = self.get_serializer(chat)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Отмечает все сообщения в чате как прочитанные.
        POST /api/chats/{id}/mark_read/
        """
        chat = self.get_object()
        # Отмечаем все непрочитанные сообщения от другого участника как прочитанные
        Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': 'ok'})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с сообщениями.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает сообщения чата"""
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            # Проверяем, что пользователь является участником чата
            chat = get_object_or_404(
                Chat.objects.filter(
                    Q(participant1=self.request.user) | Q(participant2=self.request.user)
                ),
                id=chat_id
            )
            return Message.objects.filter(chat=chat).select_related('sender').prefetch_related('attachments').order_by('created_at')
        return Message.objects.none()
    
    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор"""
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_create(self, serializer):
        """Создает сообщение"""
        message = serializer.save(sender=self.request.user)
        
        # Обрабатываем загрузку файлов
        files = self.request.FILES
        if files:
            for key, file in files.items():
                if key.startswith('file_'):
                    FileAttachment.objects.create(
                        message=message,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        mime_type=file.content_type or 'application/octet-stream'
                    )
        
        # Обновляем дату последнего сообщения в чате
        message.chat.last_message_at = timezone.now()
        message.chat.save(update_fields=['last_message_at'])
        
        # Перезагружаем сообщение с вложениями
        message.refresh_from_db()
    
    def get_serializer_context(self):
        """Добавляет request в контекст сериализатора"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для получения списка пользователей (сотрудников с Contact).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Возвращает всех активных пользователей, у которых есть Contact"""
        # Фильтруем только активных пользователей с связанным Contact
        queryset = User.objects.filter(
            contact__isnull=False,
            is_active=True
        ).select_related('contact').order_by('username')
        
        # Поиск по имени, username или email
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(contact__full_name__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Возвращает информацию о текущем пользователе"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@login_required
def chat_view(request):
    """
    Представление для страницы чата.
    """
    context = {
        'current_user': json.dumps({
            'id': request.user.id,
            'username': request.user.username,
        })
    }
    return render(request, 'messaging/chat.html', context)
