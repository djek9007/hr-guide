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
            
        # Проверяем, что у текущего пользователя есть доступ к чату
        if not request.user.contact.chat_access:
            return Response({'error': 'У вас нет доступа к чату'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Получаем пользователя и проверяем, что он является сотрудником (имеет Contact)
            other_user = User.objects.select_related('contact').get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
        
        # Проверяем, что другой пользователь является сотрудником
        if not hasattr(other_user, 'contact') or other_user.contact is None:
            return Response({'error': 'Можно создавать чаты только с сотрудниками'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Проверяем, что у другого пользователя есть доступ к чату
        if not other_user.contact.chat_access:
            return Response({'error': 'У выбранного сотрудника нет доступа к чату'}, status=status.HTTP_403_FORBIDDEN)
        
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
        Уведомляет отправителя (другого участника) через WebSocket,
        чтобы он видел статус «прочитано» в реальном времени.
        """
        chat = self.get_object()
        # Выбираем непрочитанные сообщения от другого участника (не от текущего пользователя)
        to_mark = Message.objects.filter(
            chat=chat,
            is_read=False
        ).exclude(
            sender=request.user
        )
        # Сохраняем ID до обновления для WebSocket-уведомления
        message_ids = list(to_mark.values_list('id', flat=True))
        read_at = timezone.now()

        to_mark.update(is_read=True, read_at=read_at)

        # Уведомляем отправителя прочитанных сообщений через WebSocket,
        # чтобы у него в UI обновились галочки «прочитано»
        if message_ids:
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Другой участник = тот, кто отправил прочитанные сообщения
                    other = chat.get_other_participant(request.user)
                    other_group = f"user_{other.id}"
                    async_to_sync(channel_layer.group_send)(
                        other_group,
                        {
                            'type': 'messages_read',
                            'chat_id': chat.id,
                            'message_ids': message_ids,
                            'read_at': read_at.isoformat(),
                        }
                    )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f'Не удалось отправить уведомление messages_read: {e}'
                )

        return Response({'status': 'ok'})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с сообщениями.
    Ленивая загрузка: при GET list — последние 50 сообщений; при ?before_id=ID — более старые 50.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Используем кастомную пагинацию в list()
    
    # Размер страницы для ленивой загрузки (сообщений за один запрос)
    MESSAGES_PAGE_SIZE = 50

    def list(self, request, *args, **kwargs):
        """
        Список сообщений чата с ленивой загрузкой.
        - GET /api/messages/?chat_id=X — последние MESSAGES_PAGE_SIZE сообщений (хронологический порядок).
        - GET /api/messages/?chat_id=X&before_id=ID — более старые 50 сообщений (id < before_id).
        Ответ: { "results": [...], "has_older": bool }.
        """
        queryset = self.filter_queryset(self.get_queryset())
        chat_id = request.query_params.get('chat_id')
        if not chat_id:
            return Response({'results': [], 'has_older': False})
        
        before_id = request.query_params.get('before_id')
        limit = self.MESSAGES_PAGE_SIZE
        
        if before_id:
            try:
                before_id = int(before_id)
            except (TypeError, ValueError):
                return Response({'error': 'Некорректный before_id'}, status=status.HTTP_400_BAD_REQUEST)
            # Более старые сообщения: id < before_id, выбираем limit+1 для проверки has_older
            msgs = list(queryset.filter(id__lt=before_id).order_by('-id')[:limit + 1])
        else:
            # Первая загрузка: последние (новейшие) limit сообщений
            msgs = list(queryset.order_by('-id')[:limit + 1])
        
        has_older = len(msgs) > limit
        if has_older:
            msgs = msgs[:limit]
        # msgs: от новых к старым; для отображения (хронология) — реверс
        msgs = list(reversed(msgs))
        
        serializer = self.get_serializer(msgs, many=True)
        return Response({'results': serializer.data, 'has_older': has_older})
    
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
        Сотрудники должны иметь chat_access=True.
        """
        # Фильтруем только активных пользователей с связанным Contact (сотрудников)
        queryset = User.objects.filter(
            contact__isnull=False,      # Только пользователи с Contact (сотрудники)
            contact__chat_access=True,  # Только сотрудники с доступом к чату
            is_active=True              # Только активные пользователи
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

    @action(detail=False, methods=['post'], url_path='me/avatar')
    def update_avatar(self, request):
        """
        Загрузка и обновление аватарки текущего сотрудника.
        Принимает: avatar (файл изображения), crop (строка "x1,y1,x2,y2" — опционально).
        Сотрудник должен иметь связанный Contact.
        """
        # Проверяем, что у пользователя есть контакт (он сотрудник)
        if not hasattr(request.user, 'contact') or request.user.contact is None:
            return Response(
                {'error': 'Только сотрудники с записью в справочнике могут менять аватарку.'},
                status=status.HTTP_403_FORBIDDEN
            )
        contact = request.user.contact

        # Проверяем наличие файла
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response(
                {'error': 'Выберите изображение для загрузки.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверка типа файла (только изображения)
        allowed_types = ('image/jpeg', 'image/png', 'image/gif', 'image/webp')
        if avatar_file.content_type and avatar_file.content_type not in allowed_types:
            return Response(
                {'error': 'Допустимы только форматы: JPG, PNG, GIF, WebP.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ограничение размера (5 МБ)
        if avatar_file.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'Размер файла не должен превышать 5 МБ.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # crop — строка "x1,y1,x2,y2" от Cropper.js (crop_corners в easy-thumbnails ожидает этот формат)
        # Берём из POST; для DRF при multipart fallback на request.data
        crop = (request.POST.get('crop') or getattr(request, 'data', {}).get('crop') or '').strip()

        try:
            # Очищаем кэш easy-thumbnails для старого аватара до удаления файла,
            # чтобы старые thumbnail-URL не отдавали устаревшее при повторных запросах
            if contact.avatar:
                try:
                    from easy_thumbnails.files import get_thumbnailer
                    get_thumbnailer(contact.avatar).delete_thumbnails()
                except Exception:
                    pass
                contact.avatar.delete(save=False)
            # Сохраняем новое изображение
            contact.avatar = avatar_file
            # Записываем координаты кропа в формате x1,y1,x2,y2 (лево, верх, право, низ)
            if crop:
                contact.avatar_cropping = crop
            else:
                contact.avatar_cropping = ''
            contact.save()
        except Exception as e:
            return Response(
                {'error': f'Ошибка при сохранении: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Формируем абсолютный URL новой аватарки для ответа
        avatar_url = contact.get_cropped_avatar_url(size=(80, 80))
        if avatar_url and request:
            avatar_url = request.build_absolute_uri(avatar_url)
        return Response({'avatar_url': avatar_url})


@login_required
def chat_view(request):
    """
    Представление для страницы чата.
    """
    # Проверяем доступ к чату
    if hasattr(request.user, 'contact') and request.user.contact:
        if not request.user.contact.chat_access:
             return render(request, 'messaging/no_access.html')
    else:
        # Если не сотрудник (нет контакта), тоже нет доступа
        # Но по ТЗ "когда пользователь переходить в чат", скорее всего он уже сотрудник
        # Если админ без контакта - пускаем? Наверное нет, чат для сотрудников
        # Если это суперюзер без контакта, можно пустить посмотреть, но он не сможет участвовать
        if not request.user.is_superuser:
            return render(request, 'messaging/no_access.html')

    context = {
        'current_user': json.dumps({
            'id': request.user.id,
            'username': request.user.username,
        })
    }
    return render(request, 'messaging/chat.html', context)
