### Контекст проекта
Мы продолжаем развивать мультитенантную SaaS-платформу лояльности для ресторанов на Django и Vue 3. 
Текущая задача: Добавить генерацию цифровых карт лояльности для **Google Wallet** (Google Pay) без использования сторонних платных сервисов.

### Архитектура Google Wallet API для SaaS
В Google Wallet сущности делятся на две части:
1. **LoyaltyClass (Класс карты):** Описывает общие правила для шаблона карты конкретного ресторана (Название заведения, Логотип, Цвета, Ссылка на сайт). Создается один раз для каждой организации (`Organization`).
2. **LoyaltyObject (Объект карты):** Индивидуальная карта конкретного гостя (`Customer`). Содержит его имя, баланс бонусов, штрих-код/QR-код с его ID и ссылку на класс.

Для генерации карт на бэкенде мы будем использовать JWT-подпись (Json Web Token) с использованием ключа Сервисного Аккаунта Google Cloud. При клике на кнопку во Vue, бэкенд генерирует JWT-ссылку, по которой Google нативно открывает окно "Сохранить в Google Кошелек".

---

### ТРЕБОВАНИЯ К РЕАЛИЗАЦИИ

#### 1. Расширение моделей Django
В приложении `core` (или `integrations`) дополнить модели:

**Модель `Organization` (Настройки Google Wallet на уровне ресторана):**
- `google_issuer_id` (CharField, max_length=50, null=True, blank=True) — ID издателя из Google Pay & Wallet Console.
- `google_loyalty_class_id` (CharField, max_length=100, null=True, blank=True) — Уникальный ID шаблона карты этого ресторана в Google (формат: `issuer_id.class_id`).

**Модель `Customer` (Данные карты гостя):**
- `google_wallet_object_id` (CharField, max_length=100, null=True, blank=True) — Уникальный ID экземпляра карты гостя в Google (формат: `issuer_id.customer_id`).

#### 2. Сервисный слой для работы с Google Wallet API (Python)
Создать сервис `services/google_wallet_service.py`. Для генерации JWT-ссылок использовать библиотеку `PyJWT` (или официальную `google-auth`).

Сервис должен содержать метод `generate_google_wallet_link(customer: Customer, current_balance: int) -> str`:
1. Метод берет сервисный ключ Google Cloud (хранится в `settings.GOOGLE_SERVICE_ACCOUNT_JSON` или подтягивается динамически).
2. Формирует структуру `LoyaltyObject` согласно Google API (программа лояльности, имя клиента, баланс бонусов, тип штрих-кода — QR_CODE, где зашит `customer.id` или телефон).
3. Упаковывает объект в JWT-payload, подписывает его закрытым ключом сервисного аккаунта и формирует валидную ссылку вида:
   `https://pay.google.com/gp/v/save/{JWT_TOKEN}`

#### 3. API Эндпоинт в DRF
Создать эндпоинт `/api/loyalty/customer/wallet/google/` (доступ только авторизованным в TMA клиентам):
- Метод: `GET` или `POST`.
- Логика: Бэкенд берет текущего `Customer`, запрашивает актуальный баланс бонусов из локального кэша БД (или делает быстрый запрос в iiko Cloud, если интеграция уже включена), генерирует JWT-ссылку через `GoogleWalletService` и возвращает её на фронтенд.

#### 4. Фронтенд (Vue 3 Telegram Mini App)
На Главном экране Личного Кабинета активировать кнопку **"Добавить в Google Wallet"**:
- Кнопка должна отображаться, только если пользователь зашел с Android-устройства (проверка через `window.Telegram.WebApp.platform === 'android'` или `navigator.userAgent`).
- По клику на кнопку отправляется запрос на бэкенд эндпоинт `/api/loyalty/customer/wallet/google/`.
- Полученную ссылку Mini App открывает во внешнем браузере или нативно через Telegram SDK: `window.Telegram.WebApp.openLink(url)`.

---

### ЧТО ОЖИДАЕТСЯ НА ВЫХОДЕ:
1. Миграции для моделей с новыми полями для Google Wallet.
2. Файл `google_wallet_service.py` с логикой формирования JWT-payload для Loyalty-карт без использования внешних оберток, на чистом `PyJWT` или встроенных инструментах.
3. Эндпоинт в DRF для выдачи ссылки.
4. Vue 3 компонент кнопки "Save to Google Wallet", соответствующий официальным гайдлайнам Google по стилю (черная/белая брендированная кнопка).