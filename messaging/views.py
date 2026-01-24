# -*- coding: utf-8 -*-
import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth.models import User
from django.db.models import Q, Max
from .models import Chat, Message, FileAttachment
from .serializers import ChatSerializer, MessageSerializer, MessageCreateSerializer, UserSerializer, FileAttachmentSerializer
from contacts.models import Contact
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class ChatViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с чатами.
    """
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Возвращает чаты текущего пользователя.
        Только чаты между сотрудниками (пользователями с Contact).
        """
        user = self.request.user
        # Фильтруем чаты, где оба участника являются сотрудниками (имеют Contact)
        return Chat.objects.filter(
            Q(participant1=user) | Q(participant2=user),
            is_active=True,
            participant1__contact__isnull=False,  # Участник 1 должен быть сотрудником
            participant2__contact__isnull=False    # Участник 2 должен быть сотрудником
        ).select_related('participant1__contact', 'participant2__contact').annotate(
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
        Работает только с сотрудниками (пользователями с Contact).
        GET /api/chats/get_or_create/?user_id=123
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем, что текущий пользователь является сотрудником
        if not hasattr(request.user, 'contact') or request.user.contact is None:
            return Response({'error': 'Только сотрудники могут создавать чаты'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Получаем пользователя и проверяем, что он является сотрудником (имеет Contact)
            other_user = User.objects.select_related('contact').get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, что другой пользователь является сотрудником
        if not hasattr(other_user, 'contact') or other_user.contact is None:
            return Response({'error': 'Можно создавать чаты только с сотрудниками'}, status=status.HTTP_400_BAD_REQUEST)
        
        if other_user == request.user:
            return Response({'error': 'Нельзя создать чат с самим собой'}, status=status.HTTP_400_BAD_REQUEST)
        
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
    pagination_class = None  # Отключаем пагинацию для сообщений - нужно видеть все сообщения чата
    
    def get_queryset(self):
        """
        Возвращает сообщения чата.
        Только для чатов между сотрудниками (пользователями с Contact).
        """
        chat_id = self.request.query_params.get('chat_id')
        if chat_id:
            # Проверяем, что пользователь является участником чата и оба участника - сотрудники
            chat = get_object_or_404(
                Chat.objects.filter(
                    Q(participant1=self.request.user) | Q(participant2=self.request.user),
                    participant1__contact__isnull=False,  # Участник 1 должен быть сотрудником
                    participant2__contact__isnull=False   # Участник 2 должен быть сотрудником
                ),
                id=chat_id
            )
            return Message.objects.filter(chat=chat).select_related('sender', 'sender__contact').prefetch_related('attachments').order_by('created_at')
        return Message.objects.none()
    
    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор"""
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def perform_create(self, serializer):
        """
        Создает сообщение.
        Только сотрудники (пользователи с Contact) могут отправлять сообщения.
        """
        # Проверяем, что отправитель является сотрудником
        if not hasattr(self.request.user, 'contact') or self.request.user.contact is None:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Только сотрудники могут отправлять сообщения')
        
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
        
        # Отправляем сообщение обоим участникам чата через WebSocket (channel_layer)
        # Это гарантирует доставку сообщения, даже если WebSocket нестабилен
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                # Сериализуем сообщение для отправки
                message_serializer = MessageSerializer(message, context={'request': self.request})
                message_data = message_serializer.data
                
                # Отправляем сообщение обоим участникам чата
                participant1_group = f"user_{message.chat.participant1_id}"
                participant2_group = f"user_{message.chat.participant2_id}"
                
                # Отправляем асинхронно, чтобы не блокировать ответ API
                import logging
                logger = logging.getLogger(__name__)
                
                try:
                    logger.info(f'Отправка сообщения через channel_layer участнику 1: {participant1_group}, chat_id: {message.chat.id}')
                    async_to_sync(channel_layer.group_send)(
                        participant1_group,
                        {
                            'type': 'chat_message',
                            'message': message_data,
                            'chat_id': message.chat.id
                        }
                    )
                    logger.info(f'Сообщение успешно отправлено участнику 1: {participant1_group}')
                except Exception as e1:
                    logger.warning(f'Не удалось отправить сообщение участнику 1 ({participant1_group}): {e1}', exc_info=True)
                
                try:
                    logger.info(f'Отправка сообщения через channel_layer участнику 2: {participant2_group}, chat_id: {message.chat.id}')
                    async_to_sync(channel_layer.group_send)(
                        participant2_group,
                        {
                            'type': 'chat_message',
                            'message': message_data,
                            'chat_id': message.chat.id
                        }
                    )
                    logger.info(f'Сообщение успешно отправлено участнику 2: {participant2_group}')
                except Exception as e2:
                    logger.warning(f'Не удалось отправить сообщение участнику 2 ({participant2_group}): {e2}', exc_info=True)
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning('Channel layer недоступен, сообщение не будет отправлено через WebSocket')
        except Exception as e:
            # Если не удалось отправить через channel_layer, это не критично
            # Сообщение уже сохранено в БД и будет загружено при следующем обновлении
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Не удалось отправить сообщение через channel_layer: {e}')
    
    def get_serializer_context(self):
        """Добавляет request в контекст сериализатора"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class UserListPagination(PageNumberPagination):
    """
    Пагинация для списка пользователей в чате.
    Позволяет запрашивать больше 20 записей через page_size для полного списка
    и серверного поиска по ФИО.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 2000


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для получения списка пользователей.
    Возвращает только сотрудников (пользователей с Contact).
    Поддерживает ?search= для поиска по ФИО, username, email по всей БД.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = UserListPagination

    def get_queryset(self):
        """
        Возвращает всех активных пользователей, у которых есть Contact.
        Только сотрудники могут быть в списке для чата.
        """
        # Фильтруем только активных пользователей с связанным Contact (сотрудников)
        queryset = User.objects.filter(
            contact__isnull=False,  # Только пользователи с Contact (сотрудники)
            is_active=True          # Только активные пользователи
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
