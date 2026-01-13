"""
Команда Django для импорта контактов из DOCX файла.
Использование: python manage.py import_contacts phone.docx
"""
import docx
import re
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from contacts.models import Department, Position, Room, Contact


class Command(BaseCommand):
    help = 'Импортирует контакты из DOCX файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            nargs='?',
            default='phone.docx',
            help='Путь к DOCX файлу со справочником (по умолчанию: phone.docx)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить существующие данные перед импортом',
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        try:
            # Открываем DOCX файл
            self.stdout.write(f'Открываем файл: {file_path}')
            doc = docx.Document(file_path)
            
            if not doc.tables:
                raise CommandError('В документе не найдено таблиц')
            
            table = doc.tables[0]
            
            self.stdout.write(self.style.SUCCESS(f'Найдена таблица: {len(table.rows)} строк, {len(table.columns)} столбцов'))
            
            if options['clear']:
                self.stdout.write(self.style.WARNING('Очистка существующих данных...'))
                Contact.objects.all().delete()
                Room.objects.all().delete()
                Position.objects.all().delete()
                Department.objects.all().delete()
            
            # Словари для кэширования созданных объектов
            departments_cache = {}
            positions_cache = {}
            rooms_cache = {}
            current_department = None
            
            imported_count = 0
            updated_count = 0
            skipped_count = 0
            
            with transaction.atomic():
                # Пропускаем заголовки (первые 16-17 строк содержат заголовки)
                start_row = 16  # Начинаем с строки, где появляются реальные данные
                
                for row_idx in range(start_row, len(table.rows)):
                    row = table.rows[row_idx]
                    cells = [cell.text.strip() for cell in row.cells]
                    
                    # Пропускаем пустые строки
                    if not any(cells):
                        continue
                    
                    # Определяем тип строки
                    room_number = cells[0] if len(cells) > 0 else ''
                    
                    # Если это заголовок отдела (нет номера кабинета, но есть текст в первой колонке)
                    # Проверяем, не является ли это названием отдела
                    if room_number and not re.match(r'^\d+$', room_number) and len(room_number) > 3:
                        # Проверяем, не является ли это названием отдела (например, "Хатшылық")
                        if not any(cell.isdigit() for cell in cells[:3] if cell):
                            # Это может быть название отдела
                            dept_name_ru = room_number
                            dept_name_kk = cells[1] if len(cells) > 1 and cells[1] else None
                            
                            # Создаем или получаем отдел
                            if dept_name_ru not in departments_cache:
                                department, created = Department.objects.get_or_create(
                                    name_ru=dept_name_ru,
                                    defaults={'name_kk': dept_name_kk or ''}
                                )
                                departments_cache[dept_name_ru] = department
                                current_department = department
                            else:
                                current_department = departments_cache[dept_name_ru]
                            continue
                    
                    # Если нет номера кабинета (цифры), пропускаем
                    if not room_number or not re.match(r'^\d+$', room_number):
                        continue
                    
                    # Извлекаем данные
                    # Колонка 1-10: должность (дублируется на разных языках)
                    position_ru = None
                    position_kk = None
                    
                    # Ищем должность в колонках 1-10
                    for i in range(1, min(11, len(cells))):
                        cell_text = cells[i]
                        if cell_text and len(cell_text) > 2:
                            # Первая найденная должность - русская
                            if not position_ru:
                                position_ru = cell_text.replace('\n', ' ').strip()
                            # Если следующая отличается и длиннее - это может быть казахская версия
                            elif cell_text != position_ru and len(cell_text) > len(position_ru) * 0.8:
                                if not position_kk:
                                    position_kk = cell_text.replace('\n', ' ').strip()
                    
                    # Колонка 12: ФИО
                    full_name = cells[12] if len(cells) > 12 and cells[12] else None
                    if full_name:
                        full_name = full_name.replace('\n', ' ').strip()
                    
                    # Колонка 13: рабочий телефон
                    work_phone = cells[13] if len(cells) > 13 and cells[13] else None
                    if work_phone:
                        work_phone = work_phone.replace('\n', ' ').strip()
                    
                    # Колонка 14: мобильный телефон
                    mobile_phone = cells[14] if len(cells) > 14 and cells[14] else None
                    if mobile_phone:
                        mobile_phone = mobile_phone.replace('\n', ' ').strip()
                    
                    # Пропускаем если нет ФИО
                    if not full_name or len(full_name) < 3:
                        skipped_count += 1
                        continue
                    
                    # Создаем или получаем кабинет
                    if room_number not in rooms_cache:
                        room, created = Room.objects.get_or_create(
                            number=room_number,
                            defaults={}
                        )
                        rooms_cache[room_number] = room
                    room = rooms_cache[room_number]
                    
                    # Создаем или получаем должность
                    position = None
                    if position_ru:
                        position_key = position_ru.lower().strip()
                        if position_key not in positions_cache:
                            position, created = Position.objects.get_or_create(
                                name_ru=position_ru,
                                defaults={'name_kk': position_kk or ''}
                            )
                            positions_cache[position_key] = position
                        else:
                            position = positions_cache[position_key]
                    
                    # Создаем или обновляем контакт
                    contact, created = Contact.objects.update_or_create(
                        full_name=full_name,
                        room=room,
                        defaults={
                            'position': position,
                            'department': current_department,
                            'work_phone': work_phone or '',
                            'mobile_phone': mobile_phone or '',
                        }
                    )
                    
                    if created:
                        imported_count += 1
                    else:
                        updated_count += 1
                    
                    if (imported_count + updated_count) % 50 == 0:
                        self.stdout.write(f'Обработано: {imported_count + updated_count} контактов...')
            
            self.stdout.write(self.style.SUCCESS(
                f'\n{"="*50}\n'
                f'Импорт завершен успешно!\n'
                f'{"="*50}\n'
                f'Импортировано новых контактов: {imported_count}\n'
                f'Обновлено существующих: {updated_count}\n'
                f'Пропущено строк: {skipped_count}\n'
                f'Создано отделов: {len(departments_cache)}\n'
                f'Создано должностей: {len(positions_cache)}\n'
                f'Создано кабинетов: {len(rooms_cache)}\n'
                f'Всего контактов в базе: {Contact.objects.count()}\n'
                f'{"="*50}'
            ))
            
        except FileNotFoundError:
            raise CommandError(f'Файл не найден: {file_path}')
        except Exception as e:
            import traceback
            self.stdout.write(self.style.ERROR(f'Ошибка при импорте: {str(e)}'))
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise CommandError(f'Ошибка при импорте: {str(e)}')
