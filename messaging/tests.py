from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Chat, ChatParticipant, Message
from contacts.models import Contact

class GroupChatTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.user3 = User.objects.create_user(username='user3', password='password')
        
        # Create contacts (required for chat functionality)
        Contact.objects.create(user=self.user1, full_name='User 1')
        Contact.objects.create(user=self.user2, full_name='User 2')
        Contact.objects.create(user=self.user3, full_name='User 3')
        
        self.client.force_authenticate(user=self.user1)

    def test_create_group_chat(self):
        # DRF router generates 'chat-create-group' from action 'create_group'
        url = reverse('chat-create-group')
        data = {
            'title': 'Test Group',
            'participants': [self.user2.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        chat_id = response.data['id']
        chat = Chat.objects.get(id=chat_id)
        
        self.assertEqual(chat.type, Chat.TYPE_GROUP)
        self.assertEqual(chat.title, 'Test Group')
        self.assertEqual(chat.owner, self.user1)
        
        # Check participants
        self.assertTrue(ChatParticipant.objects.filter(chat=chat, user=self.user1, role=ChatParticipant.ROLE_ADMIN).exists())
        self.assertTrue(ChatParticipant.objects.filter(chat=chat, user=self.user2, role=ChatParticipant.ROLE_MEMBER).exists())

    def test_add_participants(self):
        # Create group
        chat = Chat.objects.create(type=Chat.TYPE_GROUP, title='Group', owner=self.user1)
        ChatParticipant.objects.create(chat=chat, user=self.user1, role=ChatParticipant.ROLE_ADMIN)
        
        url = reverse('chat-add-participants', args=[chat.id])
        data = {'user_ids': [self.user2.id, self.user3.id]}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertTrue(ChatParticipant.objects.filter(chat=chat, user=self.user2).exists())
        self.assertTrue(ChatParticipant.objects.filter(chat=chat, user=self.user3).exists())

    def test_remove_participant(self):
        # Create group with 3 users
        chat = Chat.objects.create(type=Chat.TYPE_GROUP, title='Group', owner=self.user1)
        ChatParticipant.objects.create(chat=chat, user=self.user1, role=ChatParticipant.ROLE_ADMIN)
        ChatParticipant.objects.create(chat=chat, user=self.user2)
        
        url = reverse('chat-remove-participant', args=[chat.id])
        data = {'user_id': self.user2.id}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(ChatParticipant.objects.filter(chat=chat, user=self.user2).exists())

    def test_leave_group(self):
        # Create group with user1 (admin) and user2 (member)
        chat = Chat.objects.create(type=Chat.TYPE_GROUP, title='Group', owner=self.user1)
        ChatParticipant.objects.create(chat=chat, user=self.user1, role=ChatParticipant.ROLE_ADMIN)
        ChatParticipant.objects.create(chat=chat, user=self.user2, role=ChatParticipant.ROLE_MEMBER)
        
        # User 2 leaves
        self.client.force_authenticate(user=self.user2)
        url = reverse('chat-remove-participant', args=[chat.id])
        data = {'user_id': self.user2.id}
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertFalse(ChatParticipant.objects.filter(chat=chat, user=self.user2).exists())
        self.assertTrue(ChatParticipant.objects.filter(chat=chat, user=self.user1).exists())

    def test_only_participants_see_messages(self):
        # Create group with user1 and user2
        chat = Chat.objects.create(type=Chat.TYPE_GROUP, title='Group', owner=self.user1)
        ChatParticipant.objects.create(chat=chat, user=self.user1)
        ChatParticipant.objects.create(chat=chat, user=self.user2)
        
        # User 1 sends message
        Message.objects.create(chat=chat, sender=self.user1, text='Hello')
        
        # User 2 checks messages
        self.client.force_authenticate(user=self.user2)
        url = reverse('message-list')
        response = self.client.get(url, {'chat_id': chat.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # User 3 (not in chat) tries to check messages
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(url, {'chat_id': chat.id})
        # My MessageViewSet returns empty list if not participant, because I use Message.objects.none() in get_queryset
        # But wait, get_object_or_404(Chat, id=chat_id) in get_queryset might raise 404 if filter fails?
        # Let's check get_queryset logic again.
        # Chat.objects.filter(participants__user=self.request.user)
        # If user is not participant, chat is not found -> 404.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
