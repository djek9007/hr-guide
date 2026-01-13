import docx

doc = docx.Document('phone.docx')
table = doc.tables[0]

# Ищем строки с ФИО и телефонами (обычно это строки с несколькими заполненными колонками)
print('Ищем строки с данными сотрудников:\n')
found = 0
for row_idx in range(15, min(100, len(table.rows))):
    row = table.rows[row_idx]
    cells = [cell.text.strip() for cell in row.cells]
    
    # Ищем строки, где есть номер кабинета и несколько заполненных полей
    if cells[0] and any(len(cell) > 10 for cell in cells[1:]):
        print(f'Строка {row_idx+1}:')
        for i, cell in enumerate(cells):
            if cell and len(cell) > 0:
                print(f'  [{i}]: {cell[:100]}')
        print()
        found += 1
        if found >= 10:
            break
