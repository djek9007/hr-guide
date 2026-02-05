# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('announcements', '0001_initial'),
    ]

    operations = [
        # Удаляем старый индекс
        migrations.RemoveIndex(
            model_name='announcement',
            name='announcement_created_idx',
        ),
        
        # Переименовываем created_at в published_date
        migrations.RenameField(
            model_name='announcement',
            old_name='created_at',
            new_name='published_date',
        ),
        
        # Переименовываем created_by в author
        migrations.RenameField(
            model_name='announcement',
            old_name='created_by',
            new_name='author',
        ),
        
        # Изменяем поле published_date - убираем auto_now_add
        migrations.AlterField(
            model_name='announcement',
            name='published_date',
            field=models.DateTimeField(help_text='Дата и время публикации объявления', verbose_name='Дата публикации'),
        ),
        
        # Изменяем поле author
        migrations.AlterField(
            model_name='announcement',
            name='author',
            field=models.ForeignKey(help_text='Автор объявления', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Автор'),
        ),
        
        # Добавляем новый индекс
        migrations.AddIndex(
            model_name='announcement',
            index=models.Index(fields=['-published_date'], name='announcement_published_idx'),
        ),
        
        # Изменяем ordering в Meta
        migrations.AlterModelOptions(
            name='announcement',
            options={'ordering': ['-published_date'], 'verbose_name': 'Объявление', 'verbose_name_plural': 'Объявления'},
        ),
    ]
