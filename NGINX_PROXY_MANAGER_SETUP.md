# Настройка nginxproxymanager для HR Guide

## Преимущества использования nginxproxymanager

✅ **Быстрая работа по локальной сети** - nginx эффективно обслуживает статику и медиа  
✅ **Кэширование** - правильные заголовки для кэширования статики  
✅ **Сжатие** - автоматическое gzip сжатие для CSS/JS  
✅ **SSL/HTTPS** - возможность настроить HTTPS для безопасности  
✅ **Несколько доменов** - легко настроить несколько проектов  
✅ **Простота** - веб-интерфейс для настройки

## Настройка Docker Compose

### Вариант 1: nginxproxymanager в той же сети

Если nginxproxymanager запущен в Docker и использует ту же сеть:

1. Узнайте имя сети nginxproxymanager:
```bash
docker network ls
```

2. Раскомментируйте в `docker-compose.yml`:
```yaml
networks:
  - nginxproxymanager_network

# И в секции networks:
nginxproxymanager_network:
  external: true
  name: npm_default  # Замените на реальное имя сети
```

### Вариант 2: nginxproxymanager на хост-машине

Если nginxproxymanager установлен на хост-машине, порты уже закомментированы. 
Используйте `host.docker.internal` или IP контейнера в настройках nginxproxymanager.

## Настройка Proxy Host в nginxproxymanager

1. Откройте веб-интерфейс nginxproxymanager (обычно `http://IP_СЕРВЕРА:81`)

2. Перейдите в **Proxy Hosts** → **Add Proxy Host**

3. Настройте:
   - **Domain Names**: 
     - Для локальной сети: `192.168.58.86` (или доменное имя, если настроен DNS)
     - Можно добавить несколько: `hr-guide.local`, `192.168.58.86`
   
   - **Scheme**: `http`
   
   - **Forward Hostname/IP**: 
     - Если в одной сети: `hr-guide-web`
     - Если на хост-машине: `host.docker.internal` или IP контейнера
   
   - **Forward Port**: `8000`
   
   - **Cache Assets**: ✅ Включить (для ускорения статики)
   
   - **Block Common Exploits**: ✅ Включить
   
   - **Websockets Support**: ✅ Включить (если используете WebSockets)

4. На вкладке **Advanced** добавьте кастомную конфигурацию для статики и медиа (опционально):

```nginx
# Оптимизация для статики и медиа
location /static/ {
    alias /var/www/hr-guide/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
    access_log off;
}

location /media/ {
    alias /var/www/hr-guide/media/;
    expires 7d;
    add_header Cache-Control "public";
    access_log off;
}
```

⚠️ **Примечание**: Для прямого обслуживания статики через nginx нужно пробросить volumes в контейнер nginxproxymanager.

5. Сохраните настройки

## Проверка работы

1. Перезапустите контейнер:
```bash
docker-compose down
docker-compose up -d --build
```

2. Проверьте доступность:
   - Локально: `http://192.168.58.86` (или ваш домен)
   - У коллег в сети: тот же адрес должен работать

3. Проверьте консоль браузера (F12):
   - Статические файлы должны загружаться с правильными заголовками кэширования
   - Медиа файлы должны открываться корректно

## Оптимизация для статики через nginx (продвинутая настройка)

Если хотите, чтобы nginx напрямую обслуживал статику (еще быстрее):

1. В `docker-compose.yml` пробросьте volumes для nginxproxymanager:
```yaml
# Добавьте в docker-compose.yml контейнера nginxproxymanager
volumes:
  - ./staticfiles:/var/www/hr-guide/staticfiles:ro
  - ./media:/var/www/hr-guide/media:ro
```

2. В настройках Proxy Host → Advanced используйте конфигурацию выше

## WhiteNoise vs nginx

- **WhiteNoise**: Остается как fallback, если nginx недоступен
- **nginx**: Основной сервер для статики (быстрее и эффективнее)

Оба могут работать одновременно - nginx будет обрабатывать запросы первым, WhiteNoise - резервный вариант.

## Troubleshooting

### Проблема: Не открывается по сети

✅ Проверьте:
- Контейнер `hr-guide-web` запущен: `docker ps`
- Сети подключены правильно: `docker network inspect hr-guide-network`
- В nginxproxymanager правильно указан Forward Hostname/IP и Port

### Проблема: Статика не загружается

✅ Проверьте:
- Статика собрана: `docker exec hr-guide-web python manage.py collectstatic`
- Пути в nginx настроены правильно
- WhiteNoise работает как fallback (проверьте в логах)

### Проблема: Медиа файлы не открываются

✅ Проверьте:
- Volume для медиа проброшен: `./media:/app/media`
- Права доступа правильные в контейнере

## Быстрый старт

1. Убедитесь, что порты закомментированы в `docker-compose.yml` (уже сделано)
2. Настройте Proxy Host в nginxproxymanager
3. Перезапустите контейнеры
4. Проверьте работу по IP/домену

Готово! 🚀
