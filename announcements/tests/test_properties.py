"""
Property-based tests for the Announcement model using Hypothesis.

These tests verify universal properties that should hold for all valid inputs,
complementing the unit tests with broader coverage across the input space.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from hypothesis import given, settings, strategies as st
from hypothesis.extra.django import from_model, TestCase as HypothesisTestCase
from announcements.models import Announcement


class AnnouncementPropertyTests(HypothesisTestCase):
    """Property-based tests for the Announcement model"""
    
    def setUp(self):
        """Set up test data"""
        self.user, _ = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'password': 'testpass123'
            }
        )
    
    @given(
        title_kk=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        title_ru=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        content_kk=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        content_ru=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_1_published_date_required(
        self, title_kk, title_ru, content_kk, content_ru
    ):
        """
        Property 1: Обязательность даты публикации
        
        **Validates: Requirements 1.1**
        
        For any new announcement, the published_date must be explicitly set
        and should not be automatically generated.
        """
        # Create announcement with generated data and explicit published_date
        published_date = timezone.now()
        announcement = Announcement.objects.create(
            title_kk=title_kk,
            title_ru=title_ru,
            content_kk=content_kk,
            content_ru=content_ru,
            published_date=published_date,
            author=self.user
        )
        
        # Property assertions
        # 1. published_date must not be None
        self.assertIsNotNone(
            announcement.published_date,
            "published_date should be set on creation"
        )
        
        # 2. published_date should match what we set
        self.assertEqual(
            announcement.published_date, published_date,
            f"published_date should match the explicitly set value"
        )
        
        # Clean up
        announcement.delete()
    
    @given(
        field_to_empty=st.sampled_from(['title_kk', 'title_ru', 'content_kk', 'content_ru']),
        title_kk=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        title_ru=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        content_kk=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        content_ru=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_property_2_required_fields_validation(
        self, field_to_empty, title_kk, title_ru, content_kk, content_ru
    ):
        """
        Property 2: Валидация обязательных полей
        
        **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4**
        
        For any attempt to create or update an announcement with an empty value
        in any of the required fields (title_kk, title_ru, content_kk, content_ru),
        the operation should be rejected with a validation error.
        """
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError
        
        # Prepare valid data
        data = {
            'title_kk': title_kk,
            'title_ru': title_ru,
            'content_kk': content_kk,
            'content_ru': content_ru,
            'published_date': timezone.now(),
            'author': self.user
        }
        
        # Empty the selected field
        data[field_to_empty] = ''
        
        # Property assertion: Creating announcement with empty required field should fail
        with self.assertRaises((ValidationError, IntegrityError, ValueError)) as context:
            announcement = Announcement(**data)
            announcement.full_clean()  # Trigger Django validation
            announcement.save()
        
        # Verify that the announcement was not created
        self.assertEqual(
            Announcement.objects.filter(author=self.user).count(),
            0,
            f"Announcement with empty {field_to_empty} should not be created"
        )
    
    @given(
        title_kk=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        title_ru=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(blacklist_characters='\x00')
        ),
        # Generate safe HTML content with common formatting tags
        html_content=st.one_of(
            # Simple text in paragraph
            st.text(
                min_size=1, 
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                    blacklist_characters='\x00<>&"'
                )
            ).map(lambda s: f"<p>{s}</p>"),
            # Bold text
            st.text(
                min_size=1, 
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                    blacklist_characters='\x00<>&"'
                )
            ).map(lambda s: f"<p><strong>{s}</strong></p>"),
            # Italic text
            st.text(
                min_size=1, 
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                    blacklist_characters='\x00<>&"'
                )
            ).map(lambda s: f"<p><em>{s}</em></p>"),
            # Unordered list
            st.lists(
                st.text(
                    min_size=1, 
                    max_size=50,
                    alphabet=st.characters(
                        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                        blacklist_characters='\x00<>&"'
                    )
                ),
                min_size=1,
                max_size=3
            ).map(lambda items: "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"),
            # Link
            st.tuples(
                st.text(
                    min_size=1, 
                    max_size=50,
                    alphabet=st.characters(
                        whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                        blacklist_characters='\x00<>&"'
                    )
                ),
                st.from_regex(r'https?://[a-z0-9\-\.]+\.[a-z]{2,}', fullmatch=True)
            ).map(lambda t: f'<p><a href="{t[1]}">{t[0]}</a></p>'),
            # Mixed formatting
            st.text(
                min_size=1, 
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'),
                    blacklist_characters='\x00<>&"'
                )
            ).map(lambda s: f"<p><strong>{s}</strong> <em>text</em></p>"),
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_property_3_html_formatting_preservation(
        self, title_kk, title_ru, html_content
    ):
        """
        Property 3: Сохранение HTML-форматирования (Round-trip)
        
        **Validates: Requirements 1.6**
        
        For any announcement with HTML formatting in content fields, after saving
        to the database and reading it back, the formatting should be preserved
        (safe HTML tags remain unchanged).
        """
        # Create announcement with HTML content in both languages
        announcement = Announcement.objects.create(
            title_kk=title_kk,
            title_ru=title_ru,
            content_kk=html_content,
            content_ru=html_content,
            published_date=timezone.now(),
            author=self.user
        )
        
        # Get the ID to fetch from database
        announcement_id = announcement.id
        
        # Clear any cached data by deleting the object from memory
        del announcement
        
        # Fetch the announcement from database (round-trip)
        retrieved_announcement = Announcement.objects.get(id=announcement_id)
        
        # Property assertions: HTML formatting should be preserved
        # The content should contain the HTML tags we put in
        self.assertIn(
            '<', retrieved_announcement.content_kk,
            "HTML tags should be preserved in content_kk"
        )
        self.assertIn(
            '<', retrieved_announcement.content_ru,
            "HTML tags should be preserved in content_ru"
        )
        
        # The original HTML content should be preserved (allowing for CKEditor sanitization)
        # We check that the core structure is maintained
        if '<p>' in html_content:
            self.assertIn(
                '<p>', retrieved_announcement.content_kk,
                "Paragraph tags should be preserved"
            )
        if '<strong>' in html_content:
            self.assertIn(
                '<strong>', retrieved_announcement.content_kk,
                "Strong tags should be preserved"
            )
        if '<em>' in html_content:
            self.assertIn(
                '<em>', retrieved_announcement.content_kk,
                "Emphasis tags should be preserved"
            )
        if '<ul>' in html_content:
            self.assertIn(
                '<ul>', retrieved_announcement.content_kk,
                "List tags should be preserved"
            )
        if '<li>' in html_content:
            self.assertIn(
                '<li>', retrieved_announcement.content_kk,
                "List item tags should be preserved"
            )
        if '<a href=' in html_content:
            self.assertIn(
                '<a', retrieved_announcement.content_kk,
                "Link tags should be preserved"
            )
        
        # The content should match what we saved (with possible CKEditor normalization)
        # We verify the essential content is the same
        self.assertEqual(
            retrieved_announcement.content_kk, html_content,
            "Content in Kazakh should be preserved exactly after round-trip"
        )
        self.assertEqual(
            retrieved_announcement.content_ru, html_content,
            "Content in Russian should be preserved exactly after round-trip"
        )
        
        # Clean up
        retrieved_announcement.delete()
    
    @given(
        title_kk=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(
                blacklist_characters='\x00',
                blacklist_categories=('Cs',)  # Exclude surrogate characters
            )
        ),
        title_ru=st.text(
            min_size=1, 
            max_size=255,
            alphabet=st.characters(
                blacklist_characters='\x00',
                blacklist_categories=('Cs',)  # Exclude surrogate characters
            )
        ),
        content_kk=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(
                blacklist_characters='\x00',
                blacklist_categories=('Cs',)  # Exclude surrogate characters
            )
        ),
        content_ru=st.text(
            min_size=1, 
            max_size=1000,
            alphabet=st.characters(
                blacklist_characters='\x00',
                blacklist_categories=('Cs',)  # Exclude surrogate characters
            )
        ),
        # Generate a datetime offset in days from today
        days_offset=st.integers(min_value=-365, max_value=365)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_10_is_new_determination(
        self, title_kk, title_ru, content_kk, content_ru, days_offset
    ):
        """
        Property 10: Определение нового объявления
        
        **Validates: Requirements 5.2**
        
        For any announcement, the is_new() method should return True if and only if
        the announcement's publication date (published_date.date()) equals the current date.
        """
        # Manually set published_date to a specific date based on days_offset
        target_datetime = timezone.now() + timedelta(days=days_offset)
        
        # Create announcement with valid data
        announcement = Announcement.objects.create(
            title_kk=title_kk,
            title_ru=title_ru,
            content_kk=content_kk,
            content_ru=content_ru,
            published_date=target_datetime,
            author=self.user
        )
        
        # Refresh from database to ensure we have the updated value
        announcement.refresh_from_db()
        
        # Get current date for comparison
        current_date = timezone.now().date()
        announcement_date = announcement.published_date.date()
        
        # Property assertion: is_new() should return True IFF published_date.date() == current date
        expected_is_new = (announcement_date == current_date)
        actual_is_new = announcement.is_new()
        
        self.assertEqual(
            actual_is_new, expected_is_new,
            f"is_new() returned {actual_is_new} but expected {expected_is_new}. "
            f"Announcement date: {announcement_date}, Current date: {current_date}, "
            f"Days offset: {days_offset}"
        )
        
        # Additional verification: if is_new() returns True, the date must be today
        if actual_is_new:
            self.assertEqual(
                announcement_date, current_date,
                f"is_new() returned True but announcement date ({announcement_date}) "
                f"is not equal to current date ({current_date})"
            )
        
        # Additional verification: if is_new() returns False, the date must not be today
        if not actual_is_new:
            self.assertNotEqual(
                announcement_date, current_date,
                f"is_new() returned False but announcement date ({announcement_date}) "
                f"is equal to current date ({current_date})"
            )
        
        # Clean up
        announcement.delete()
