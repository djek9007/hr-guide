"""
Unit tests for the Announcement model.

These tests verify the basic functionality of the Announcement model,
including field validation, the is_new() method, and model creation.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from announcements.models import Announcement


class AnnouncementModelTest(TestCase):
    """Test cases for the Announcement model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_announcement_with_all_fields(self):
        """Test creating an announcement with all required fields"""
        announcement = Announcement.objects.create(
            title_kk="Тест хабарландыру",
            title_ru="Тестовое объявление",
            content_kk="<p>Бұл тест мазмұны</p>",
            content_ru="<p>Это тестовое содержимое</p>",
            published_date=timezone.now(),
            author=self.user
        )
        
        self.assertEqual(announcement.title_kk, "Тест хабарландыру")
        self.assertEqual(announcement.title_ru, "Тестовое объявление")
        self.assertEqual(announcement.content_kk, "<p>Бұл тест мазмұны</p>")
        self.assertEqual(announcement.content_ru, "<p>Это тестовое содержимое</p>")
        self.assertEqual(announcement.author, self.user)
        self.assertIsNotNone(announcement.published_date)
    
    def test_published_date_can_be_set(self):
        """Test that published_date can be manually set"""
        custom_date = timezone.now() - timedelta(days=5)
        announcement = Announcement.objects.create(
            title_kk="Тест",
            title_ru="Тест",
            content_kk="<p>Тест</p>",
            content_ru="<p>Тест</p>",
            published_date=custom_date,
            author=self.user
        )
        
        self.assertIsNotNone(announcement.published_date)
        self.assertEqual(announcement.published_date, custom_date)
    
    def test_is_new_returns_true_for_today(self):
        """Test that is_new() returns True for announcements published today"""
        announcement = Announcement.objects.create(
            title_kk="Жаңа хабарландыру",
            title_ru="Новое объявление",
            content_kk="<p>Мазмұн</p>",
            content_ru="<p>Содержимое</p>",
            published_date=timezone.now(),
            author=self.user
        )
        
        self.assertTrue(announcement.is_new())
    
    def test_is_new_returns_false_for_old_announcement(self):
        """Test that is_new() returns False for announcements published in the past"""
        past_date = timezone.now() - timedelta(days=1)
        announcement = Announcement.objects.create(
            title_kk="Ескі хабарландыру",
            title_ru="Старое объявление",
            content_kk="<p>Мазмұн</p>",
            content_ru="<p>Содержимое</p>",
            published_date=past_date,
            author=self.user
        )
        
        self.assertFalse(announcement.is_new())
    
    def test_str_returns_russian_title(self):
        """Test that __str__ returns the Russian title"""
        announcement = Announcement.objects.create(
            title_kk="Қазақша тақырып",
            title_ru="Русский заголовок",
            content_kk="<p>Мазмұн</p>",
            content_ru="<p>Содержимое</p>",
            published_date=timezone.now(),
            author=self.user
        )
        
        self.assertEqual(str(announcement), "Русский заголовок")
    
    def test_ordering_by_published_date_desc(self):
        """Test that announcements are ordered by published_date in descending order"""
        # Create three announcements with different publication dates
        now = timezone.now()
        
        announcement1 = Announcement.objects.create(
            title_kk="Бірінші",
            title_ru="Первое",
            content_kk="<p>1</p>",
            content_ru="<p>1</p>",
            published_date=now - timedelta(hours=2),
            author=self.user
        )
        
        announcement2 = Announcement.objects.create(
            title_kk="Екінші",
            title_ru="Второе",
            content_kk="<p>2</p>",
            content_ru="<p>2</p>",
            published_date=now - timedelta(hours=1),
            author=self.user
        )
        
        announcement3 = Announcement.objects.create(
            title_kk="Үшінші",
            title_ru="Третье",
            content_kk="<p>3</p>",
            content_ru="<p>3</p>",
            published_date=now,
            author=self.user
        )
        
        # Get all announcements
        announcements = list(Announcement.objects.all())
        
        # The most recent should be first
        self.assertEqual(announcements[0].id, announcement3.id)
        self.assertEqual(announcements[1].id, announcement2.id)
        self.assertEqual(announcements[2].id, announcement1.id)
    
    def test_html_formatting_preserved(self):
        """Test that HTML formatting is preserved in content fields"""
        html_content_kk = "<p><strong>Қалың</strong> және <em>курсив</em> мәтін</p>"
        html_content_ru = "<p><strong>Жирный</strong> и <em>курсив</em> текст</p>"
        
        announcement = Announcement.objects.create(
            title_kk="HTML тест",
            title_ru="HTML тест",
            content_kk=html_content_kk,
            content_ru=html_content_ru,
            published_date=timezone.now(),
            author=self.user
        )
        
        # Refresh from database
        announcement.refresh_from_db()
        
        self.assertEqual(announcement.content_kk, html_content_kk)
        self.assertEqual(announcement.content_ru, html_content_ru)
