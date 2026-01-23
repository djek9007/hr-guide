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
        from .serializers import MessageSerializer
        
        chat_id = data.get('chat_id')
        text = data.get('text', '').strip()
        
        if not chat_id or not text:
            return
        
        # Создаем сообщение
        message = await self.create_message(chat_id, text)
        
        if message:
            # Сериализуем сообщение
            serializer = MessageSerializer(message, context={'request': None})
            message_data = serializer.data
            
            # Отправляем сообщение обоим участникам чата
            chat = await self.get_chat(chat_id)
            if chat:
                participant1_group = f"user_{chat.participant1_id}"
                participant2_group = f"user_{chat.participant2_id}"
                
                await self.channel_layer.group_send(
                    participant1_group,
                    {
                        'type': 'chat_message',
                        'message': message_data,
                        'chat_id': chat_id
                    }
                )
                await self.channel_layer.group_send(
                    participant2_group,
                    {
                        'type': 'chat_message',
                        'message': message_data,
                        'chat_id': chat_id
                    }
                )
    
    async def handle_typing(self, data):
        """Обработка индикатора печати"""
        chat_id = data.get('chat_id')
        is_typing = data.get('is_typing', False)
        
        if not chat_id:
            return
        
        chat = await self.get_chat(chat_id)
        if chat:
            # Отправляем индикатор печати другому участнику
            other_participant = chat.participant1 if chat.participant2 == self.user else chat.participant2
            other_group = f"user_{other_participant.id}"
            
            await self.channel_layer.group_send(
                other_group,
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
    
    @database_sync_to_async
    def create_message(self, chat_id, text):
        """Создает сообщение в базе данных"""
        from .models import Chat, Message
        from .serializers import MessageSerializer
        
        try:
            chat = Chat.objects.get(id=chat_id)
            # Проверяем, что пользователь является участником чата
            if chat.participant1 != self.user and chat.participant2 != self.user:
                return None
            
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                text=text
            )
            
            # Обновляем дату последнего сообщения в чате
            chat.last_message_at = timezone.now()
            chat.save(update_fields=['last_message_at'])
            
            # Загружаем связанные данные
            message = Message.objects.select_related('sender').prefetch_related('attachments').get(id=message.id)
            return message
        except Chat.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_chat(self, chat_id):
        """Получает чат из базы данных"""
        from .models import Chat
        
        try:
            return Chat.objects.select_related('participant1', 'participant2').get(id=chat_id)
        except Chat.DoesNotExist:
            return None
