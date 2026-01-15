"""Анализ структуры документа для понимания иерархии департаментов и отделов"""
import docx
import re

doc = docx.Document('phone.docx')
table = doc.tables[0]

print("=" * 80)
print("АНАЛИЗ СТРУКТУРЫ ДОКУМЕНТА")
print("=" * 80)
print()

# Ищем структуру: департаменты, отделы, сотрудники
current_level = None
departments = []
departments_with_children = {}

for row_idx in range(0, min(200, len(table.rows))):
    row = table.rows[row_idx]
    cells = [cell.text.strip() for cell in row.cells]
    
    if not any(cells):
        continue
    
    room_number = cells[0] if len(cells) > 0 else ''
    
    # Проверяем, является ли это заголовком отдела/департамента
    # (нет цифр в первой колонке, но есть текст)
    if room_number and not re.match(r'^\d+$', room_number):
        # Проверяем, есть ли в других колонках номера кабинетов
        has_room_numbers = any(re.match(r'^\d+$', cell) for cell in cells[1:15] if cell and len(cell) < 5)
        
        if not has_room_numbers:
            # Это может быть название департамента/отдела
            dept_name = room_number.replace('\n', ' ').strip()
            if len(dept_name) > 3:
                print(f"Строка {row_idx+1}: [{current_level}] {dept_name}")
                
                # Проверяем следующие строки, чтобы понять уровень вложенности
                # Смотрим следующие 5 строк
                next_rows_have_rooms = False
                for next_idx in range(row_idx + 1, min(row_idx + 6, len(table.rows))):
                    next_cells = [cell.text.strip() for cell in table.rows[next_idx].cells]
                    if next_cells and re.match(r'^\d+$', next_cells[0]):
                        next_rows_have_rooms = True
                        break
                
                if next_rows_have_rooms:
                    # Есть сотрудники сразу после - это отдел
                    level = "ОТДЕЛ"
                    if dept_name not in departments_with_children:
                        departments_with_children[dept_name] = []
                else:
                    # Нет сотрудников сразу - возможно департамент
                    level = "ДЕПАРТАМЕНТ?"
                    if dept_name not in departments:
                        departments.append(dept_name)
                
                current_level = dept_name
                print(f"  -> Тип: {level}")
        else:
            # Есть номера кабинетов в строке - это данные сотрудника
            if room_number and re.match(r'^\d+$', room_number):
                full_name = cells[12] if len(cells) > 12 and cells[12] else None
                if full_name:
                    print(f"Строка {row_idx+1}: [СОТРУДНИК] Кабинет {room_number}, {full_name[:50]}")

print()
print("=" * 80)
print("НАЙДЕННЫЕ ДЕПАРТАМЕНТЫ/ОТДЕЛЫ:")
print("=" * 80)
for dept in departments:
    print(f"  - {dept}")
