@echo off
echo ==================================================
echo Импорт данных из phone.docx
echo ==================================================
echo.

if not exist phone.docx (
    echo Ошибка: Файл phone.docx не найден!
    echo Убедитесь, что файл phone.docx находится в корне проекта.
    pause
    exit /b 1
)

python manage.py import_contacts phone.docx --clear

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==================================================
    echo Импорт завершен успешно!
    echo ==================================================
) else (
    echo.
    echo Ошибка при импорте!
)

pause
