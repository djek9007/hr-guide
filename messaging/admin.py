# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import Chat, ChatParticipant, Message, FileAttachment


class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 1
    autocomplete_fields = ['user']


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'title_display', 'owner', 'created_at', 'last_message_at', 'is_active']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['title', 'owner__username']
    readonly_fields = ['created_at', 'last_message_at']
    date_hierarchy = 'created_at'
    inlines = [ChatParticipantInline]
    autocomplete_fields = ['owner']
    
    def title_display(self, obj):
        return str(obj)
    title_display.short_description = 'Название / Участники'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'text_preview', 'created_at', 'is_read', 'read_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['text', 'sender__username']
    readonly_fields = ['created_at', 'read_at']
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        if obj.text:
            return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
        return '-'
    text_preview.short_description = 'Текст'


@admin.register(FileAttachment)
class FileAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'original_filename', 'file_size', 'uploaded_at', 'delete_after']
    list_filter = ['uploaded_at', 'delete_after']
    search_fields = ['original_filename', 'message__text']
    readonly_fields = ['uploaded_at']
    date_hierarchy = 'uploaded_at'
