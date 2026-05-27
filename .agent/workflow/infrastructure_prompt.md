# Техническое задание: Инфраструктура, Docker Compose, Celery и интеграция с iiko Cloud

## 1. Стек контейнеризации и инфраструктура
Проект должен полностью разворачиваться в изолированном окружении с помощью Docker и Docker Compose. 

### 1.1. Архитектура сервисов (docker-compose.yml)
Необходимо настроить 7 основных сервисов:
1. `db` (PostgreSQL) — СУБД для хранения данных SaaS.
2. `redis` (Redis) — Используется для:
   - Кэширования токенов доступа iiko API (15-минутный TTL).
   - Брокера сообщений Celery.
   - Хранения состояний каналов Django Channels (WebSocket channel layer).
3. `backend` (Django / ASGI / Daphne) — HTTP API и WebSockets.
4. `celery-worker` (Celery) — Воркер для выполнения фоновых задач (регистрация клиентов в iiko, синхронизация баллов, рассылка).
5. `celery-beat` (Celery Beat) — Планировщик периодических задач.
6. `frontend-admin` (Nginx + Vue 3 Admin) — Сборка и раздача статики панели управления.
7. `frontend-tma` (Nginx + Vue 3 TMA) — Сборка и раздача статики Telegram Mini App.

---

## 2. Docker Compose и Docker-файлы (Шаблоны)

### 2.1. Шаблон `docker-compose.yml`
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: loyalty_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file: .env
    # Порт БД не пробрасывается наружу ради безопасности

  redis:
    image: redis:7-alpine
    container_name: loyalty_redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    # Порт Redis не пробрасывается наружу

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: loyalty_backend
    command: daphne -b 0.0.0.0 -p 8000 config.asgi:application
    volumes:
      - ./backend:/app
      - media_data:/app/media
    depends_on:
      - db
      - redis
    env_file: .env
    # Порт бэкенда 8000 скрыт внутри сети Docker, все запросы идут через nginx

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: loyalty_celery_worker
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
      - media_data:/app/media
    depends_on:
      - db
      - redis
    env_file: .env

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: loyalty_celery_beat
    command: celery -A config beat -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file: .env

  # Единая точка входа. Раздает фронтенд (Admin + TMA) и проксирует запросы на бэкенд
  nginx:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: loyalty_nginx
    ports:
      - "6054:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - media_data:/app/media:ro
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  media_data:
```

### 2.2. Многоэтапный Dockerfile для фронтенда (`frontend/Dockerfile`)
Этот файл собирает оба Vue 3 приложения (Admin Panel и TMA) в единый Nginx контейнер:
```dockerfile
# Этап 1: Сборка Admin Panel
FROM node:20-alpine AS build-admin
WORKDIR /app/admin
COPY admin/package*.json ./
RUN npm install
COPY admin/ ./
RUN npm run build

# Этап 2: Сборка Telegram Mini App (TMA)
FROM node:20-alpine AS build-tma
WORKDIR /app/tma
COPY tma/package*.json ./
RUN npm install
COPY tma/ ./
RUN npm run build

# Этап 3: Финальный образ Nginx
FROM nginx:alpine AS final
# Размещаем Admin Panel в корне
COPY --from=build-admin /app/admin/dist /usr/share/nginx/html
# Размещаем TMA по вложенному пути /tma
COPY --from=build-tma  /app/tma/dist  /usr/share/nginx/html/tma
```

### 2.3. Конфигурационный файл Nginx (`nginx/nginx.conf`)
Обеспечивает маршрутизацию, обработку веб-сокетов (`/ws/`), проксирование API-запросов и скрытие панели администратора Django под префикс `/administrator/`:
```nginx
server {
    listen 80;
    client_max_body_size 20M;

    # 1. Telegram Mini App (под префиксом /tma/)
    location /tma/ {
        alias /usr/share/nginx/html/tma/;
        try_files $uri $uri/ /tma/index.html;
    }

    # 2. REST API бэкенда
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 3. Django Admin Panel (скрыта под /administrator/)
    location /administrator/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 4. Статика Django Admin
    location /static/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 5. Веб-сокеты (Django Channels / Daphne)
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 6. Медиа-файлы (загруженные логотипы и т.д.)
    location /media/ {
        alias /app/media/;
    }

    # 7. Панель управления Admin Panel (SPA в корне сайта)
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

### 2.4. Dockerfile для Бэкенда (`backend/Dockerfile`)
```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
```

---

## 3. Интеграция с iiko Cloud: Кэширование токенов в Redis

API iiko Cloud требует получения временного токена доступа (`accessToken`) через запрос авторизации. Этот токен живет ровно 15 минут.
Делать этот запрос при каждом действии клиента категорически запрещено из-за лимитов API iiko и задержки сети.

### Требование к реализации:
Реализуй менеджер токенов iiko, использующий Redis в качестве кэша:
- Ключ в Redis: `iiko_token_<organization_id>`.
- Время жизни (TTL) в кэше: 13-14 минут.
- При запросе к iiko API: менеджер сначала проверяет наличие токена в Redis. Если токена нет, делает запрос `POST /api/1/access_token`, сохраняет его в Redis с TTL 14 минут и возвращает.

**Пример структуры сервиса на бэкенде:**
```python
import django_redis
import requests
from django.core.cache import cache

class IikoAuthService:
    def __init__(self, organization):
        self.org = organization
        self.cache_key = f"iiko_token_{self.org.id}"

    def get_access_token(self) -> str:
        # Пытаемся получить токен из Redis
        token = cache.get(self.cache_key)
        if token:
            return token

        # Если в кэше нет, запрашиваем у iiko
        url = f"{self.org.iiko_api_base_url}/access_token"
        payload = {"apiLogin": self.org.iiko_api_login}
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        token = response.json().get("token")
        
        # Сохраняем в кэш Redis с таймаутом 14 минут (840 секунд)
        cache.set(self.cache_key, token, timeout=840)
        return token
```

---

## 4. Архитектура фоновых задач Celery (iiko Customer Sync)

Интеграция с iiko должна выполняться асинхронно, чтобы сетевые задержки внешнего API не блокировали работу вебхуков Telegram и HTTP-запросов клиентов.

### 4.1. Задача 1: Асинхронная регистрация клиента в iiko Cloud (`tasks.sync_customer_to_iiko`)
**Триггер:** Успешное получение телефона клиента через Telegram Webhook.
**Действие:**
1. После того как `TmaWebhookView` записал телефон в модель `Customer`, бэкенд запускает задачу Celery:
   `sync_customer_to_iiko.delay(customer_id)`
2. Задача Celery:
   - Получает `Customer` по `id`.
   - Через `IikoAuthService` берет токен доступа.
   - Делает запрос в iiko Cloud `POST /api/1/loyalty/iiko/customer/info` для поиска гостя по номеру телефона.
   - Если гость найден: сохраняет его `iiko_customer_id` (UUID) в БД.
   - Если гость не найден: делает запрос `POST /api/1/loyalty/iiko/customer/create_or_update`, передавая имя, фамилию и телефон. Полученный `iiko_customer_id` записывает в модель `Customer`.
   - Если запрос завершился сетевой ошибкой — задача должна автоматически перезапуститься через механизмы `self.retry` с экспоненциальной задержкой.

**Пример задачи:**
```python
from config.celery import app
from apps.loyalty.models import Customer
import logging

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_customer_to_iiko(self, customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        auth_service = IikoAuthService(customer.organization)
        token = auth_service.get_access_token()
        
        # Логика отправки данных в iiko
        # ...
        # customer.iiko_customer_id = response_uuid
        # customer.save(update_fields=['iiko_customer_id'])
        
    except Exception as exc:
        logger.error(f"Error syncing customer {customer_id} to iiko: {exc}")
        raise self.retry(exc=exc)
```

### 4.2. Задача 2: Периодическая синхронизация баланса баллов (`tasks.sync_all_customers_points`)
**Триггер:** Расписание Celery Beat (например, каждые 2 часа ночью).
**Действие:**
1. Задача выбирает всех активных клиентов `Customer`, у которых заполнен `iiko_customer_id`.
2. Для каждого клиента делает запрос в iiko Cloud для получения актуального баланса баллов лояльности.
3. Обновляет внутренний кэш баланса (если будет создана соответствующая колонка в БД) или отправляет пуш-уведомление пользователю, если количество баллов изменилось.

---

## 5. Шаблон переменных окружения (.env.example)

Для успешной работы всех контейнеров, WebSockets, Celery и интеграций в корневой директории нового проекта должен быть создан файл `.env`. Ниже представлена структура переменных окружения с описанием каждого параметра:

```ini
# --- НАСТРОЙКИ СУБД (POSTGRESQL) ---
POSTGRES_DB=loyalty_db
POSTGRES_USER=loyalty_user
POSTGRES_PASSWORD=secure_postgres_password_here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# --- НАСТРОЙКИ DJANGO БЭКЕНДА ---
DJANGO_SECRET_KEY=django-insecure-generate-a-long-random-secret-key-here
DJANGO_DEBUG=1 # 1 для разработки, 0 для продакшна
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend,*.ngrok-free.dev,yourdomain.com

# Доверенные источники для обхода защиты CSRF при работе через прокси/туннели (ngrok, cloudflare tunnel и т.д.)
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://localhost:3001,https://*.ngrok-free.dev,https://yourdomain.com

# Локализация времени для корректных отчетов и отправки рассылок
TIME_ZONE=Asia/Almaty

# --- НАСТРОЙКИ КЭШИРОВАНИЯ И БРОКЕРА (REDIS) ---
# Используется как брокер для Celery, кэш токенов iiko и backend для Django Channels
REDIS_URL=redis://redis:6379/0

# --- ШИФРОВАНИЕ ЧУВСТВИТЕЛЬНЫХ ДАННЫХ В БД ---
# Ключ для шифрования API-токенов интеграций (iiko API-ключи, Kaspi токены и т.д.) в базе данных. 
# Должен быть 32-байтовым base64-ключом. Можно сгенерировать через: cryptography.fernet.Fernet.generate_key()
FIELD_ENCRYPTION_KEY=yqymH0qmsVeH6oQiJ2SNnoZZvOBAu8vum3pXvykfnkE=

# --- НАСТРОЙКИ Telegram Webhook ---
# Базовый домен для регистрации вебхуков Telegram (должен поддерживать HTTPS, например, ngrok в разработке)
WEBHOOK_DOMAIN=https://your-public-domain.ngrok-free.dev

# --- НАСТРОЙКИ ФРОНТЕНДА ---
# Базовый URL бэкенда для запросов Axios из Vue.js приложений
VITE_API_BASE_URL=https://your-public-domain.ngrok-free.dev/api
```

