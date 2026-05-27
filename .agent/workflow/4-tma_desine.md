🎨 Анатомия идеального экрана карты в TMA
Экраны лояльности уровня Starbucks или Додо Пицца строятся по вертикальной структуре (сверху вниз), где каждый блок решает свою задачу.
1. Шапка (Header) — Контекст заведения
Элементы: Небольшой круглый логотип ресторана, название филиала (или текущего города), и кнопка настроек/профиля.
UX-фишка: Если пользователь перешел по QR-коду конкретного столика, в шапке можно мягко подсветить: «Вы в Mevent Coffee на Абая • Стол №4».
2. Главный герой: Виртуальная карта (The Hero Card)
Это центральный элемент экрана. Не нужно делать её скучным прямоугольником. Сделай её «живой»:
Соотношение сторон: Классическая банковская карта (около 1.58 : 1), с мягкими скругленными углами (rounded-2xl в Tailwind).
Фон (Задний план): Используй градиент или размытое абстрактное изображение (стеклянный эффект / Glassmorphism) в фирменных цветах тенанта. Например, для кофейни — глубокий кофейно-шоколадный градиент, для азиатского ресторана — неоновый темный неон.
Данные на карте:
Крупно (Главный фокус): Баланс бонусов. Например: 1 250 ₸ или 450 баллов. Слово «бонусов» сделай чуть меньшим шрифтом под цифрой.
Мелко в углу: Имя гостя (Aigerim) и его статус/категория в iiko (например, «Silver статус • 5% кэшбэк» или «New User»).
Индикатор прогресса (Progress Bar): Прямо внутри карты или сразу под ней размести тонкую анимированную линию. Она показывает, сколько бонусов или заказов осталось до перехода на следующий уровень лояльности в iiko (например, до статуса «Gold • 10%»).
3. Блок кассира: Динамический QR-код (The Scanner Zone)
Чтобы кассир на кассе iiko Front мог применить лояльность, QR-код должен быть крупным и доступным в один клик.
Дизайн: Белый скругленный квадрат, по центру которого расположен сам QR-код. Для премиальности в самый центр QR-кода можно встроить мини-логотип ресторана.
UX-фишка (Яркость экрана): При открытии Mini App или при нажатии на QR-код, приложение должно автоматически вызывать метод Telegram.WebApp.requestWriteAccess() или нативно поднимать яркость экрана телефона на 100% (если это доступно в SDK), чтобы сканер на кассе считал код даже через поцарапанное стекло смартфона.
Подсказка для гостя: Под QR-кодом напиши блеклым шрифтом: «Покажите этот код кассиру перед оплатой».
4. Футер (Нижняя часть) — Wallet и Быстрые действия
Кнопки Wallet: Две аккуратные брендированные плашки «Добавить в Google Кошелек» (и Apple Wallet на будущее) по официальным гайдлайнам корпораций. На Android-устройствах показываем только Google Wallet.
История операций: Небольшой раскрывающийся список (аккордеон) с последними 3 транзакциями из iiko:
«+120 б. за заказ №1422»
«-500 б. списание»
🛠 Пример верстки карточки на Tailwind CSS (для твоего Vue 3 фронтенда)
Этот компонент динамически подтягивает цвета организации (branding.primary_color, branding.gradient_to) из Pinia-стора, которые ты заложил в SaaS-панели бэкенда.
Фрагмент кода
<template>
  <div class="w-full max-w-md mx-auto p-4 space-y-6">
    
    <!-- Виртуальная карта лояльности -->
    <div 
      :style="{ backgroundImage: `linear-gradient(135deg, ${branding.primary_color}, ${branding.gradient_to})` }"
      class="relative overflow-hidden rounded-2xl p-6 text-white shadow-xl transition-all duration-300"
    >
      <!-- Фоновый декоративный круг для объема -->
      <div class="absolute -right-10 -bottom-10 w-40 h-40 bg-white/10 rounded-full blur-xl"></div>
      
      <!-- Верхний ряд карты -->
      <div class="flex justify-between items-start mb-8">
        <div>
          <p class="text-xs text-white/70 uppercase tracking-wider font-medium">Баланс карты</p>
          <h3 class="text-4xl font-bold mt-1 tracking-tight">
            {{ customer.balance }} <span class="text-xl font-normal text-white/80">б.</span>
          </h3>
        </div>
        <span class="px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold uppercase tracking-wider">
          {{ customer.category_name || 'Новичок' }}
        </span>
      </div>

      <!-- Нижний ряд карты -->
      <div class="flex justify-between items-end mt-4">
        <div>
          <p class="text-xs text-white/60">Участник</p>
          <p class="text-sm font-medium tracking-wide">{{ customer.name }}</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-white/60">Кэшбэк</p>
          <p class="text-sm font-bold">{{ customer.cashback_percent }}%</p>
        </div>
      </div>
    </div>

    <!-- Зона сканирования QR-кода -->
    <div class="bg-white dark:bg-zinc-900 rounded-2xl p-6 shadow-md flex flex-col items-center justify-center border border-zinc-100 dark:border-zinc-800">
      <div class="p-3 bg-white rounded-xl shadow-inner border border-zinc-50">
        <!-- Компонент qrcode.vue -->
        <qrcode-vue :value="customer.iiko_id || customer.phone" :size="180" level="H" />
      </div>
      <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-4 text-center">
        Покажите QR-код кассиру для начисления или списания бонусов
      </p>
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue';
import QrcodeVue from 'qrcode.vue';

// Имитация данных из твоего Pinia Store (Tenant & Customer)
const branding = ref({
  primary_color: '#4F46E5', // Динамический цвет ресторана (например, Indigo)
  gradient_to: '#06B6D4',   // Второй цвет для премиального градиента
});

const customer = ref({
  name: 'Aigerim',
  phone: '+77771858667',
  balance: 120,
  category_name: 'new_user',
  cashback_percent: 5,
  iiko_id: '03bf0000-6bec-ac1f-bcec-08deb7355f7f'
});
</script>
🎨 Микро-анимации и Темная тема: Правило хорошего тона
Поддержка Нативной Темной Темы: Если пользователь переключает Telegram в ночной режим, фон самого Mini App должен становиться глубоким графитовым/черным (bg-zinc-950), а блок вокруг QR-кода — темно-серым (bg-zinc-900). Сама карта лояльности при этом остается цветной и яркой, создавая красивый контраст.
Haptic Feedback (Виброотклик): Используй Telegram SDK для вызова легкой вибрации смартфона при открытии приложения или клике на QR-код:
JavaScript
if (window.Telegram?.WebApp?.HapticFeedback) {
    window.Telegram.WebApp.HapticFeedback.impactOccurred('light');
}

   Это создает ощущение дорогого, качественного физического продукта (как в Apple Pay).

Этот интерфейс выглядит минималистично, дорого и не перегружает гостя лишней информацией, при этом полностью закрывая техническую задачу iiko по идентификации клиента.