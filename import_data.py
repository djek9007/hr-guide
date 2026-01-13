#!/usr/bin/env python
"""
Простой скрипт для импорта данных из phone.docx

Использование:
    python import_data.py
    
Или напрямую через команду Django:
    python manage.py import_contacts phone.docx --clear
"""
import os
import sys

if __name__ == '__main__':
    print("=" * 50)
    print("Импорт данных из phone.docx")
    print("=" * 50)
    print("\nДля импорта выполните команду:")
    print("  python manage.py import_contacts phone.docx --clear")
    print("\nИли используйте батник для Windows:")
    print("  import_data.bat")
    print("=" * 50)
    
    # Проверяем наличие файла
    file_path = 'phone.docx'
    if not os.path.exists(file_path):
        print(f"\nОшибка: Файл {file_path} не найден!")
        print("Убедитесь, что файл phone.docx находится в корне проекта.")
        sys.exit(1)
    
    # Предлагаем запустить команду
    response = input("\nЗапустить импорт сейчас? (y/n): ").strip().lower()
    if response == 'y':
        print("\nЗапуск импорта...\n")
        os.system(f'python manage.py import_contacts {file_path} --clear')
    else:
        print("\nИмпорт отменен.")
