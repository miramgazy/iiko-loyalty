# Техническое задание: Разработка мультитенантного SaaS-бэкенда программы лояльности (Django + DRF + Channels)

## 1. Стек технологий и архитектура
- **Язык**: Python 3.11+
- **Фреймворк**: Django 4.2+ (LTS) / Django REST Framework (DRF)
- **Асинхронность**: Django Channels 4.0+ (для WebSockets), Daphne
- **База данных**: PostgreSQL (Single Database, Shared Schema). Во всех бизнес-моделях должен присутствовать внешний ключ `organization_id` (за исключением глобальных суперпользователей).
- **Кэш и брокер сообщений**: Redis (для Django Channels layer и сессий)
- **Авторизация**: PyJWT / django-rest-framework-simplejwt (с кастомной поддержкой авторизации как сотрудников, так и клиентов TMA).

---

## 2. Проектирование базы данных (Модели)

### 2.1. Модель Организации (Tenant) — `apps.core.models.Organization`
Каждая организация представляет собой отдельного клиента (ресторанную сеть).
```python
from django.db import models

class Organization(models.Model):
    name = models.CharField("Название ресторана/сети", max_length=255)
    slug = models.SlugField("Уникальный Slug", max_length=100, unique=True)
    address = models.TextField("Фактический адрес", blank=True)
    
    # Telegram Bot интеграция
    tg_bot_token = models.CharField("Токен Telegram-бота", max_length=255, unique=True)
    tg_bot_username = models.CharField(
        "Username Telegram-бота (без @)", 
        max_length=100, 
        unique=True, 
        db_index=True
    )
    tma_name = models.CharField("Короткое имя Mini App в BotFather", max_length=100, blank=True)
    
    # iiko Cloud API интеграция
    iiko_api_base_url = models.URLField(
        "iiko API Base URL", 
        default="https://api-ru.iiko.services/api/1"
    )
    iiko_api_login = models.CharField("iiko API Login (API-ключ)", max_length=255, blank=True)
    iiko_organization_id = models.UUIDField("iiko Organization ID", null=True, blank=True)
    iiko_loyalty_program_id = models.UUIDField("iiko Loyalty Program ID", null=True, blank=True)
    
    # Кастомизация Mini App
    branding = models.JSONField(
        "Настройки брендинга (цвета, логотип, приветствие)",
        default=dict,
        blank=True,
        help_text="Пример: {'design_color': '#FF5733', 'greeting_text': 'Добро пожаловать в Бургерную!'}"
    )
    
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_tma_link(self):
        if self.tg_bot_username and self.tma_name:
            return f"https://t.me/{self.tg_bot_username}/{self.tma_name}"
        return ""

    def __str__(self):
        return self.name
```

### 2.2. Кастомный User и ролевая модель (RBAC) — `apps.accounts.models`
Сотрудники панели управления авторизуются по логину/паролю. Связь с организациями должна поддерживать работу пользователя в нескольких ресторанах (мультитенантность).
```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Глобальные суперпользователи Django (is_superuser=True) имеют доступ ко всему SaaS
    phone = models.CharField("Телефон сотрудника", max_length=20, blank=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class UserOrganization(models.Model):
    ROLE_SUPERUSER = 'superuser'      # Разработчик / Владелец SaaS
    ROLE_SUPERADMIN = 'superadmin'    # Администратор платформы (поддержка)
    ROLE_ORG_MANAGER = 'org_manager'  # Владелец / Управляющий конкретной ресторанной сети
    ROLE_ORG_ADMIN = 'org_admin'      # Администратор конкретной точки / ресторана
    
    ROLE_CHOICES = [
        (ROLE_SUPERUSER, 'SuperUser'),
        (ROLE_SUPERADMIN, 'SuperAdmin'),
        (ROLE_ORG_MANAGER, 'OrgManager'),
        (ROLE_ORG_ADMIN, 'OrgAdmin'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, Q(is_staff=True), related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='staff_memberships')
    role = models.CharField("Роль в организации", max_length=20, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = ('user', 'organization')
```

### 2.3. Модель Клиента Лояльности (Customer) — `apps.loyalty.models.Customer`
Клиенты регистрируются через Telegram Mini App. Они привязаны к конкретной `Organization`. В рамках одной организации клиент с конкретным `telegram_id` или `phone` уникален, но глобально в базе могут существовать записи с одинаковым `telegram_id` для разных сетей (изоляция тенантов).
```python
class Customer(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='customers')
    telegram_id = models.BigIntegerField("Telegram ID")
    phone = models.CharField("Номер телефона", max_length=20, blank=True, null=True)
    iiko_customer_id = models.UUIDField("iiko Customer UUID", null=True, blank=True)
    
    # Личные данные
    first_name = models.CharField("Имя", max_length=150, blank=True)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    email = models.EmailField("E-mail", blank=True, null=True)
    birthday = models.DateField("Дата рождения", null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"
        # Уникальные индексы в рамках тенанта (организации)
        unique_together = (
            ('organization', 'telegram_id'),
            ('organization', 'phone'),
        )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone or 'Нет телефона'}) - {self.organization.name}"
```

---

## 3. Права доступа (DRF Permissions)
Создай файл `apps.accounts.permissions.py` с классами контроля доступа:
- `IsSuperUser`: Доступ только при `request.user.is_superuser == True`.
- `IsSuperAdmin`: Доступ у ролей `superuser` и `superadmin`.
- `IsOrgManager`: Доступ у управляющего организацией. Права проверяются путем извлечения `organization_id` из параметров запроса (`view.kwargs` или `request.data`) и сопоставления его с записью в `UserOrganization` для текущего `request.user`.

---

## 4. Эндпоинты API и авторизация TMA

### 4.1. Авторизация клиентов по Telegram initData
Реализуй эндпоинт `POST /api/accounts/tma/auth/`.
Фронтенд отправляет:
```json
{
  "initData": "query_id=XXXX&user=YYYY&hash=ZZZZ",
  "bot_username": "my_restaurant_bot"
}
```
**Алгоритм бэкенда:**
1. Найти `Organization` по `tg_bot_username=bot_username` (активную). Если не найдена — 404.
2. Извлечь `tg_bot_token` этой организации.
3. Проверить валидность подписи `hash` в `initData` по алгоритму Telegram:
   - Распарсить строку `initData` в словарь параметров, исключить `hash`.
   - Отсортировать ключи по алфавиту и собрать строку формата: `key1=value1\nkey2=value2`.
   - Рассчитать секретный ключ: `HMAC-SHA256(key=b"WebAppData", msg=tg_bot_token).digest()`.
   - Рассчитать итоговый хэш: `HMAC-SHA256(key=secret_key, msg=data_check_string).hexdigest()`.
   - Сравнить с присланным `hash`. Проверить `auth_date` (не старше 24 часов).
4. Если подпись невалидна — вернуть `401 Unauthorized`.
5. Если валидна: найти или создать запись `Customer` для этой `Organization` и `telegram_id` (извлеченного из объекта `user` в `initData`).
6. Сгенерировать и выдать пару JWT-токенов (Access/Refresh) для авторизованного `Customer`.
   *(Примечание: Настрой кастомный JWT Authentication Backend для поддержки аутентификации как обычных сотрудников User, так и клиентов Customer).*

### 4.3. Аутентификация сотрудников с поддержкой нескольких методов (Имя пользователя/Email или Номер телефона + Пароль)
Реализуй эндпоинт `POST /api/accounts/token/` (получение пары JWT-токенов сотрудниками) с поддержкой кастомного бэкенда аутентификации.

Бэкенд должен позволять авторизоваться по любому из следующих вариантов:
1. **Вариант 1:** Вход по Имени пользователя (`username`) или Email-адресу (`email`) + Пароль.
2. **Вариант 2:** Вход по Номеру телефона (`phone`) + Пароль. Номер телефона перед поиском в базе должен нормализоваться.

Пример реализации кастомного бэкенда аутентификации в Django (`apps.accounts.auth_backends.MultiMethodBackend`):
```python
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()

def normalize_phone(phone_str):
    # Приведение телефона к единому формату E.164, например +7XXXXXXXXXX
    digits = re.sub(r'\D', '', phone_str)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if len(digits) == 11 and digits.startswith('7'):
        return f"+{digits}"
    return phone_str

class MultiMethodBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get('email') or kwargs.get('phone')

        if not username:
            return None

        # Нормализуем телефон на случай, если введен телефон
        normalized_phone = normalize_phone(username)

        try:
            # Ищем по username, email или phone
            user = User.objects.get(
                Q(username__iexact=username) |
                Q(email__iexact=username) |
                Q(phone=normalized_phone)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```
Настрой Django для использования этого бэкенда в `settings.py`:
```python
AUTHENTICATION_BACKENDS = [
    'apps.accounts.auth_backends.MultiMethodBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

**Пример структуры ответа:**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "organization": {
    "id": 1,
    "slug": "burger-joint",
    "branding": {
      "design_color": "#FF5733",
      "greeting_text": "Привет от Шефа!"
    }
  },
  "customer": {
    "id": 42,
    "phone": "+77011112233",
    "is_onboarded": true
  }
}
```

### 4.2. Эндпоинт профиля клиента
`GET/PATCH /api/loyalty/customer/me/`
- Разрешен только авторизованным клиентам (`Customer`).
- Используется фронтендом для получения свежих данных профиля, а также для fallback-поллинга (каждые 4 секунды), если WebSocket разорван.

---

## 5. Telegram Webhook (Прием контактов)
Реализуй вебхук `POST /api/loyalty/webhook/<str:bot_token>/`.
Все созданные боты настраиваются на отправку событий на этот адрес.

**Логика работы вебхука:**
1. Найти `Organization` по `tg_bot_token=bot_token`.
2. Если в апдейте пришел объект `contact`:
   - Считать `contact.user_id` (Telegram ID) и `contact.phone_number`.
   - Нормализовать телефонный номер (привести к международному формату E.164, например, удалив лишние символы и заменив `8...` на `+7...`).
   - Найти `Customer` по паре `(organization, telegram_id)`.
   - Сохранить телефон в поле `phone` модели `Customer`.
   - Отправить WebSocket-сообщение в Django Channels group `user_<customer_id>` с событием `phone_updated` и новым телефоном.
   - С помощью Telegram Bot API отправить пользователю сообщение с подтверждением и инлайн-кнопкой для возвращения в TMA (ссылка берется из `Organization.get_tma_link()`).

---

## 6. WebSockets (Django Channels)

1. Создать WebSocket-потребитель (Consumer) на URL `ws/loyalty/user_updates/<int:customer_id>/`.
2. Добавить Middleware авторизации (JWT-токен передается в Query-параметрах `?token=XXX`). Допускать только владельца `customer_id`.
3. При подключении добавлять канал в группу `user_<customer_id>`.
4. Реализовать обработчик событий `user_update`, который отправляет данные в сокет.

**Пример отправляемого JSON при обновлении телефона:**
```json
{
  "type": "user_update",
  "message": {
    "event": "phone_updated",
    "phone": "+77011112233"
  }
}
```

---

## Что ожидается от реализации:
1. Полный набор Django-миграций для спроектированных моделей.
2. Файл `views.py` с `TmaAuthView`, `TmaWebhookView` и эндпоинтом профиля клиента.
3. Логика проверки подписи `initData` и генерации токенов.
4. Настройки ASGI (`routing.py`, `consumers.py` и middleware авторизации сокетов).
5. Логика нормализации номеров телефонов.
