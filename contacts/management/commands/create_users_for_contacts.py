# -*- coding: utf-8 -*-
"""
Команда Django для создания пользователей для существующих контактов с email.
Использование: python manage.py create_users_for_contacts
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from contacts.models import Contact


class Command(BaseCommand):
    help = 'Создает пользователей для всех контактов с email, у которых еще нет связанного пользователя'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать, что будет сделано, без фактического создания пользователей',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Находим все контакты с email, у которых нет связанного пользователя
        contacts_without_user = Contact.objects.filter(
            email__isnull=False
        ).exclude(
            email=''
        ).filter(
            user__isnull=True
        )
        
        total_count = contacts_without_user.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('Все контакты с email уже имеют связанных пользователей.'))
            return
        
        self.stdout.write(f'Найдено контактов без пользователей: {total_count}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Режим проверки (dry-run). Пользователи не будут созданы.'))
        
        created_count = 0
        linked_count = 0
        error_count = 0
        
        for contact in contacts_without_user:
            email = contact.email.strip().lower()
            
            if not email:
                continue
            
            try:
                # Проверяем, существует ли уже пользователь с таким email
                try:
                    existing_user = User.objects.get(email=email)
                    # Если пользователь существует, связываем его с контактом
                    if not dry_run:
                        contact.user = existing_user
                        contact.save(update_fields=['user'])
                    linked_count += 1
                    self.stdout.write(f'  ✓ Связан существующий пользователь для {contact.full_name} ({email})')
                    continue
                except User.DoesNotExist:
                    pass
                
                # Генерируем username из email
                username_base = email.split('@')[0]
                username = username_base
                
                # Проверяем, не занят ли username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{counter}"
                    counter += 1
                
                if not dry_run:
                    # Создаем пользователя со стандартным паролем
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='Chat2026',  # Стандартный пароль
                        is_active=True,
                        first_name=contact.full_name.split()[0] if contact.full_name else '',
                        last_name=' '.join(contact.full_name.split()[1:]) if len(contact.full_name.split()) > 1 else '',
                    )
                    
                    # Связываем пользователя с контактом
                    contact.user = user
                    contact.save(update_fields=['user'])
                
                created_count += 1
                self.stdout.write(f'  ✓ Создан пользователь для {contact.full_name} ({email}) - username: {username}')
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Ошибка для {contact.full_name} ({email}): {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n{"="*50}\n'
            f'Обработка завершена!\n'
            f'{"="*50}\n'
            f'Создано новых пользователей: {created_count}\n'
            f'Связано существующих пользователей: {linked_count}\n'
            f'Ошибок: {error_count}\n'
            f'Всего обработано: {created_count + linked_count}\n'
            f'{"="*50}'
        ))
