# -*- coding: utf-8 -*-
import os
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Chat, ChatParticipant, Message, FileAttachment
from contacts.models import Contact


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    contact_info = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'contact_info']
    
    def get_contact_info(self, obj):
        """Возвращает информацию о контакте пользователя, включая URL аватара"""
        try:
            contact = obj.contact
            # URL аватара (обрезанный) для отображения в чате, списке сотрудников и т.д.
            avatar_url = contact.get_cropped_avatar_url(size=(80, 80)) if hasattr(contact, 'get_cropped_avatar_url') else None
            request = self.context.get('request')
            if avatar_url and request:
                avatar_url = request.build_absolute_uri(avatar_url)
            return {
                'full_name': contact.full_name,
                'position': contact.position.name_ru if contact.position else None,
                'department': contact.department.name_ru if contact.department else None,
                'division': contact.division.name_ru if contact.division else None,
                'room': contact.room.number if contact.room else None,
                'avatar_url': avatar_url,
            }
        except Contact.DoesNotExist:
            return None


class FileAttachmentSerializer(serializers.ModelSerializer):
    """Сериализатор для вложений"""
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = FileAttachment
        fields = ['id', 'file', 'file_url', 'original_filename', 'file_size', 'file_size_mb', 'mime_type', 'uploaded_at']
        read_only_fields = ['uploaded_at']
    
    def get_file_url(self, obj):
        """Возвращает URL файла. None, если файла нет (удалён задачей или вручную)."""
        if not obj.file:
            return None
        # Защита: если файл уже удалён с диска — не отдаём URL, чтобы чат не вёл на 404
        try:
            if hasattr(obj.file, 'path') and not os.path.isfile(obj.file.path):
                return None
        except (OSError, ValueError):
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
    
    def get_file_size_mb(self, obj):
        """Возвращает размер файла в МБ"""
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class MessageSerializer(serializers.ModelSerializer):
    """Сериализатор для сообщений"""
    sender = UserSerializer(read_only=True)
    attachments = FileAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'chat', 'sender', 'text', 'created_at', 'is_read', 'read_at', 'attachments']
        read_only_fields = ['created_at', 'is_read', 'read_at']


class ChatParticipantSerializer(serializers.ModelSerializer):
    """Сериализатор для участника чата"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatParticipant
        fields = ['id', 'user', 'role', 'joined_at']


class ChatSerializer(serializers.ModelSerializer):
    """Сериализатор для чата"""
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id', 'type', 'title', 'owner', 'avatar', 'avatar_url',
            'participants', 'other_participant', 
            'created_at', 'last_message_at', 'is_active', 
            'last_message', 'unread_count'
        ]
        read_only_fields = ['created_at', 'last_message_at', 'owner']
    
    def get_avatar_url(self, obj):
        """Возвращает URL аватара группы"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_last_message(self, obj):
        """Возвращает последнее сообщение в чате"""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg, context=self.context).data
        return None
    
    def get_unread_count(self, obj):
        """Возвращает количество непрочитанных сообщений для текущего пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_other_participant(self, obj):
        """
        Возвращает другого участника чата (не текущего пользователя) для личных чатов.
        Для групповых чатов возвращает None.
        """
        if obj.type == Chat.TYPE_GROUP:
            return None
            
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Для личных чатов используем старую логику или ищем через участников
            other = obj.get_other_participant(request.user)
            if not other:
                # Попытка найти через ChatParticipant
                participants = obj.participants.exclude(user=request.user)
                if participants.exists():
                    other = participants.first().user
            
            if other:
                return UserSerializer(other, context=self.context).data
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания сообщения"""
    text = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Message
        fields = ['chat', 'text']
    
    def validate_chat(self, value):
        """
        Проверяет, что пользователя является участником чата.
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Проверяем участие через ChatParticipant
            is_participant = ChatParticipant.objects.filter(chat=value, user=request.user).exists()
            
            # Если не найден в ChatParticipant, проверяем старые поля (для совместимости/миграции)
            if not is_participant:
                if value.participant1 == request.user or value.participant2 == request.user:
                    is_participant = True
            
            if not is_participant:
                raise serializers.ValidationError("Вы не являетесь участником этого чата")
                
        return value
    
    def validate(self, attrs):
        """Проверяет, что есть либо текст, либо файлы"""
        request = self.context.get('request')
        text = attrs.get('text', '').strip() if attrs.get('text') else ''
        has_files = request and request.FILES
        
        if not text and not has_files:
            raise serializers.ValidationError("Сообщение должно содержать текст или файлы")
        return attrs
