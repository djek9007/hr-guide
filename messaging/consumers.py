# -*- coding: utf-8 -*-
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer для real-time сообщений в чате.
    """
    
    async def connect(self):
        """Подключение к WebSocket"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Группа для пользователя (для отправки сообщений конкретному пользователю)
        self.user_group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Отключение от WebSocket"""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
        except json.JSONDecodeError:
            pass
    
    async def handle_chat_message(self, data):
        """Обработка нового сообщения"""
        import logging
        logger = logging.getLogger(__name__)
        
        chat_id = data.get('chat_id')
        text = data.get('text', '').strip()
        
        if not chat_id or not text:
            return
        
        # Создаем сообщение
        message = await self.create_message(chat_id, text)
        
        if message:
            # Сериализуем сообщение в синхронном контексте
            message_data = await self.serialize_message(message)
            
            # Получаем участников чата
            participants = await self.get_participants(chat_id)
            
            for user_id in participants:
                group_name = f"user_{user_id}"
                try:
                    await self.channel_layer.group_send(
                        group_name,
                        {
                            'type': 'chat_message',
                            'message': message_data,
                            'chat_id': chat_id
                        }
                    )
                except Exception as e:
                    logger.error(f'Ошибка отправки сообщения в группу {group_name}: {e}', exc_info=True)
    
    async def handle_typing(self, data):
        """Обработка индикатора печати"""
        chat_id = data.get('chat_id')
        is_typing = data.get('is_typing', False)
        
        if not chat_id:
            return
        
        # Получаем участников и отправляем всем, кроме себя
        participants = await self.get_participants(chat_id)
        
        for user_id in participants:
            if user_id == self.user.id:
                continue
                
            group_name = f"user_{user_id}"
            await self.channel_layer.group_send(
                group_name,
                {
                    'type': 'typing_indicator',
                    'chat_id': chat_id,
                    'user_id': self.user.id,
                    'is_typing': is_typing
                }
            )
    
    async def chat_message(self, event):
        """Отправка сообщения клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'chat_id': event['chat_id']
        }))
    
    async def typing_indicator(self, event):
        """Отправка индикатора печати клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'chat_id': event['chat_id'],
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))

    async def messages_read(self, event):
        """
        Уведомление о прочтении.
        """
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'chat_id': event['chat_id'],
            'message_ids': event['message_ids'],
            'read_at': event.get('read_at'),
            'reader_id': event.get('reader_id')
        }))
    
    @database_sync_to_async
    def create_message(self, chat_id, text):
        """Создает сообщение в базе данных"""
        from .models import Chat, ChatParticipant, Message
        
        try:
            chat = Chat.objects.get(id=chat_id)
            # Проверяем участие
            if not ChatParticipant.objects.filter(chat=chat, user=self.user).exists():
                # Fallback check (если миграция не полная)
                if chat.type == Chat.TYPE_PRIVATE and (chat.participant1 == self.user or chat.participant2 == self.user):
                     pass
                else:
                     return None
            
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                text=text
            )
            
            chat.last_message_at = timezone.now()
            chat.save(update_fields=['last_message_at'])
            return message
        except Chat.DoesNotExist:
            return None
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Сериализует сообщение"""
        from .serializers import MessageSerializer
        from .models import Message
        
        message = Message.objects.select_related(
            'sender',
            'sender__contact',
        ).prefetch_related('attachments').get(id=message.id)
        
        if hasattr(message.sender, 'contact'):
            _ = message.sender.contact
        
        serializer = MessageSerializer(message, context={'request': None})
        return serializer.data
    
    @database_sync_to_async
    def get_participants(self, chat_id):
        """Возвращает список ID участников чата"""
        from .models import Chat, ChatParticipant
        try:
            chat = Chat.objects.get(id=chat_id)
            # Если есть ChatParticipant
            p_ids = list(ChatParticipant.objects.filter(chat=chat).values_list('user_id', flat=True))
            if not p_ids:
                # Fallback
                ids = []
                if chat.participant1_id: ids.append(chat.participant1_id)
                if chat.participant2_id: ids.append(chat.participant2_id)
                return ids
            return p_ids
        except Chat.DoesNotExist:
            return []
    
    @database_sync_to_async
    def get_chat(self, chat_id):
        """Получает чат из базы данных"""
        from .models import Chat
        try:
            return Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return None
