# Промпт для стилизации Telegram Mini App (TMA) по дизайн-системе Premium Luxury

Скопируй текст ниже и передай его агенту-разработчику для стилизации интерфейса в новом проекте.

---

## ИНСТРУКЦИЯ ПО СТИЛИЗАЦИИ И ДИЗАЙН-СИСТЕМЕ (TELEGRAM MINI APP)

Тебе необходимо реализовать стилизацию Telegram Mini App (TMA), придерживаясь премиальной дизайн-системы, использующей нативные переменные Telegram с акцентами Luxury Gold, плавными переходами и закругленными формами.

### 1. Цветовая палитра и переменные (index.css)
Используй CSS-переменные для автоматической поддержки светлой и темной тем Telegram, а также кастомного брендирования:

```css
:root {
  /* Нативные цвета Telegram WebApp */
  --tg-bg: var(--tg-theme-bg-color, #ffffff);
  --tg-text: var(--tg-theme-text-color, #111827);
  --tg-hint: var(--tg-theme-hint-color, #6b7280);
  --tg-link: var(--tg-theme-link-color, #3b82f6);
  --tg-button: var(--tg-theme-button-color, #3b82f6);
  --tg-button-text: var(--tg-theme-button-text-color, #ffffff);
  --tg-secondary-bg: var(--tg-theme-secondary-bg-color, #f3f4f6);
  --tg-header-bg: var(--tg-theme-header-bg-color, #ffffff);
  --tg-accent-text: var(--tg-theme-accent-text-color, #3b82f6);
  
  /* Фирменные золотые акценты (Luxury Gold) */
  --gold: #c9a84c; /* Может меняться динамически через JS при загрузке настроек бренда */
  --gold-dark: #a68a3c;
  --gold-light: #e0c87d;
  --gold-gradient: linear-gradient(135deg, #c9a84c 0%, #a68a3c 100%);
  --gold-glow: rgba(201, 168, 76, 0.4);
  
  /* Семантические токены */
  --bg: var(--tg-bg);
  --bg-secondary: var(--tg-secondary-bg);
  --text: var(--tg-text);
  --muted: var(--tg-hint);
  --border: rgba(0, 0, 0, 0.08);
  --card-bg: var(--tg-secondary-bg);
  --glass: rgba(255, 255, 255, 0.7);
  --text-error: #ef4444;
  
  /* Радиусы скругления и тени */
  --radius: 18px;
  --radius-sm: 12px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.1);
}

/* Переопределения для темной темы */
@media (prefers-color-scheme: dark) {
  :root {
    --tg-bg: var(--tg-theme-bg-color, #181818);
    --tg-text: var(--tg-theme-text-color, #f3f4f6);
    --tg-hint: var(--tg-theme-hint-color, #9ca3af);
    --tg-secondary-bg: var(--tg-theme-secondary-bg-color, #242424);
    --tg-header-bg: var(--tg-theme-header-bg-color, #181818);
    --border: rgba(255, 255, 255, 0.1);
    --glass: rgba(30, 30, 30, 0.75);
  }
}

html.dark {
  --tg-bg: var(--tg-theme-bg-color, #181818);
  --tg-text: var(--tg-theme-text-color, #f3f4f6);
  --tg-hint: var(--tg-theme-hint-color, #9ca3af);
  --tg-secondary-bg: var(--tg-theme-secondary-bg-color, #242424);
  --tg-header-bg: var(--tg-theme-header-bg-color, #181818);
  --border: rgba(255, 255, 255, 0.1);
  --glass: rgba(30, 30, 30, 0.75);
}
```

### 2. Макет (Layout), Ограничения и Отступы по бокам
*   **Ограничение контейнера (TMA Container):** Максимальная ширина приложения составляет `500px`. По центру экрана для десктопа:
    `max-width: 500px; margin: 0 auto; min-height: 100vh; position: relative;`
*   **Отступы страниц по бокам (Page Padding):** Внутренний отступ страниц равен строго **16px** по бокам. Нижний отступ должен составлять **100px** (чтобы контент не перекрывался нижней навигацией):
    `padding: 20px 16px 100px;`
*   **Шапка приложения (Header):**
    *   Липкая шапка (`position: sticky; top: 0; z-index: 100;`).
    *   Внутренние отступы: `padding: 12px 16px;`.
    *   Граница снизу: `border-bottom: 1px solid var(--border);`.
    *   Зазор между логотипом и текстом приветствия: `gap: 14px;`.
    *   Логотип в шапке: размеры ровно `80px` на `80px`, скругление `16px`, `object-fit: contain`, внутренний паддинг картинки `6px`.
*   **Нижняя навигация (Bottom Nav):**
    *   Фиксирована внизу: `position: fixed; bottom: 0; left: 0; right: 0;`.
    *   Высота: `calc(60px + env(safe-area-inset-bottom))`.
    *   Распределение кнопок: `display: flex; justify-content: space-around; align-items: center;`.
    *   Нижний отступ навигации обязательно учитывает safe-area: `padding-bottom: env(safe-area-inset-bottom);`.
    *   Верхняя граница: `border-top: 1px solid var(--border);`.
    *   Элементы навигации: иконки размером `24px`, зазор до текста `3px`, шрифт текста `10px`, активное состояние окрашивается в золотой градиент/цвет (`--gold`).

### 3. Размеры шрифтов и типографика (Typography)
*   **Основной шрифт:** `'Inter', -apple-system, BlinkMacSystemFont, sans-serif;`
*   **Базовый текст:** размер `16px`, межстрочный интервал `line-height: 1.5`, сглаживание `-webkit-font-smoothing: antialiased;`.
*   **Заголовки (Headers):**
    *   Для всех заголовков `h1, h2, h3` и класса `.header-font` используется уменьшенный трекинг `letter-spacing: -0.02em` и высота строки `line-height: 1.25`.
    *   `h1` (главные названия экранов): размер **26px**, вес `800` (Extra Bold).
    *   `h2` (названия крупных блоков, имя в профиле): размер **22px**, вес `700` (Bold).
    *   `h3` / Заголовки разделов (`.section-title`): размер **14px** или **16px**, вес `700`, текст в верхнем регистре (`text-transform: uppercase`), цвет золотой (`--gold`), трекинг `letter-spacing: 1px`, нижний отступ `margin-bottom: 16px`.
*   **Остальные элементы текста:**
    *   Параметры и значения строк (например, в формах или строках настроек): размер `14px` или `15px` (`font-weight: 600` или `500`).
    *   Подписи и приглушенный текст (`.text-muted`): размер **13px**, цвет `var(--muted)`.
    *   Маленькие подписи, бейджи статусов, ярлыки навигации: размер **10px**-**11px** (например, статус-бейджи: `font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;`).

### 4. Пропорции компонентов и зазоры между ними (Gaps & Proportions)
*   **Карточки (Cards):**
    *   Стандартные карточки настроек, услуг или записей: `background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px;`.
    *   Закругление карточек: ровно **18px** (`var(--radius)`).
    *   Зазор (Margin) между карточками по вертикали: строго **12px** (`margin-bottom: 12px;`).
    *   Микро-анимация при нажатии (Active State):
        `transform: scale(0.98); transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);`
*   **Кнопки (Buttons):**
    *   **Основная кнопка (`.btn-primary`):**
        *   Внутренний отступ (высота): `padding: 16px;`.
        *   Закругление: `border-radius: var(--radius-sm);` (ровно **12px**).
        *   Шрифт: размер `16px`, вес `700` (Bold).
        *   Заливка: золотой градиент `var(--gold-gradient)`. Текст кнопки черный `#000`.
        *   Тень: `box-shadow: 0 4px 15px var(--gold-glow);`.
        *   Эффект клика: `transform: scale(0.96); transition: all 0.2s;`
    *   **Второстепенная кнопка (`.btn-secondary`):**
        *   Внутренний отступ: `padding: 14px;`.
        *   Закругление: `12px` (`var(--radius-sm)`).
        *   Шрифт: размер `15px`, вес `600`, цвет `var(--text)`.
        *   Рамка: `border: 1px solid var(--border);` на фоне `var(--card-bg)`.
    *   **Кнопки действий в шапке / Иконки (`.icon-btn`, `.back-btn`):**
        *   Круглые: `border-radius: 50%;`.
        *   Кнопка «Назад»: размер `42px` на `42px`.
        *   Иконки действий в шапке: размер `36px` на `36px`.
*   
### 5. Модальные окна и нижние шторки (Bottom Sheets)
*   **Фон затемнения (Overlay):**
    `position: fixed; inset: 0; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); z-index: 500; display: flex; align-items: flex-end;`
*   **Шторка снизу (Bottom Sheet / Modal):**
    *   Выезжает снизу: `@keyframes slide-up { from { transform: translateY(100%); } to { transform: translateY(0); } }`.
    *   Ширина: `width: 100%; max-width: 500px;` (центрируется на больших экранах).
    *   Закругление верхних углов: строго **24px** (`border-radius: 24px 24px 0 0;`).
    *   Внутренние отступы: `padding: 24px 16px 40px;` (или `padding: 32px 20px 48px;` для более свободных окон).
    *   Граница сверху: `border-top: 1px solid var(--border);`.
*   **Поля ввода (Inputs) внутри шторок:**
    *   Лейбл поля: `display: block; font-size: 13px; font-weight: 600; color: var(--muted); margin-bottom: 8px;`.
    *   Поле ввода: `width: 100%; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px; padding: 12px 16px; font-size: 15px; color: var(--text); transition: all 0.2s;`. При фокусе: `border-color: var(--gold); background: var(--bg);`.