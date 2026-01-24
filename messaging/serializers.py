# -*- coding: utf-8 -*-
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Chat, Message, FileAttachment
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
        """Возвращает URL файла"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
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


class ChatSerializer(serializers.ModelSerializer):
    """Сериализатор для чата"""
    participant1 = UserSerializer(read_only=True)
    participant2 = UserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = ['id', 'participant1', 'participant2', 'other_participant', 'created_at', 'last_message_at', 'is_active', 'last_message', 'unread_count']
        read_only_fields = ['created_at', 'last_message_at']
    
    def get_last_message(self, obj):
        """Возвращает последнее сообщение в чате"""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        """Возвращает количество непрочитанных сообщений для текущего пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.filter(is_read=False).exclude(sender=request.user).count()
        return 0
    
    def get_other_participant(self, obj):
        """Возвращает другого участника чата (не текущего пользователя)"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other = obj.get_other_participant(request.user)
            return UserSerializer(other).data
        return None


class MessageCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания сообщения"""
    text = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Message
        fields = ['chat', 'text']
    
    def validate_chat(self, value):
        """
        Проверяет, что пользователь является участником чата.
        Оба участника должны быть сотрудниками (иметь Contact).
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Проверяем, что пользователь является участником чата
            if value.participant1 != request.user and value.participant2 != request.user:
                raise serializers.ValidationError("Вы не являетесь участником этого чата")
            
            # Проверяем, что оба участника являются сотрудниками (имеют Contact)
            # Чат работает только между сотрудниками
            if not hasattr(value.participant1, 'contact') or value.participant1.contact is None:
                raise serializers.ValidationError("Участник 1 не является сотрудником")
            if not hasattr(value.participant2, 'contact') or value.participant2.contact is None:
                raise serializers.ValidationError("Участник 2 не является сотрудником")
        return value
    
    def validate(self, attrs):
        """Проверяет, что есть либо текст, либо файлы"""
        request = self.context.get('request')
        text = attrs.get('text', '').strip() if attrs.get('text') else ''
        has_files = request and request.FILES
        
        if not text and not has_files:
            raise serializers.ValidationError("Сообщение должно содержать текст или файлы")
        return attrs
