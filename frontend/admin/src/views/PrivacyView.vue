<template>
  <div class="legal-page">
    <!-- Header / Navbar -->
    <header class="legal-header">
      <div class="legal-container nav-row">
        <router-link to="/" class="brand-logo">
          <div class="brand-logo-icon">M</div>
          <span class="brand-logo-text">MadiTech</span>
        </router-link>

        <nav class="nav-menu">
          <router-link to="/" class="nav-item">Главная</router-link>
          <router-link to="/#features" class="nav-item">Возможности</router-link>
          <router-link to="/#wallets" class="nav-item">Электронные кошельки</router-link>
          <router-link to="/terms" class="nav-item">Условия использования</router-link>
          <router-link to="/#contacts" class="nav-item">Контакты</router-link>
        </nav>

        <div class="nav-actions">
          <router-link :to="dashboardUrl" class="nav-btn nav-btn-outline" id="btn-privacy-login">
            <span>{{ auth.isAuthenticated ? 'В панель' : 'Войти' }}</span>
          </router-link>
          <a
            href="https://wa.me/77779285899?text=Здравствуйте!%20Хочу%20подключить%20MadiTech"
            target="_blank"
            rel="noopener noreferrer"
            class="nav-btn nav-btn-primary"
            id="btn-privacy-connect"
          >
            <span>Подключить</span>
          </a>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="legal-main">
      <div class="legal-container">
        <div class="legal-card">
          <div class="breadcrumb">
            <router-link to="/" class="back-link">← Вернуться на главную</router-link>
          </div>

          <h1 class="page-title">Политика конфиденциальности (Privacy Policy)</h1>
          <div class="meta-badge">
            <span>Дата вступления в силу: 1 января 2026 г.</span>
            <span>•</span>
            <span>Домен: <strong>loyalty.mevent.kz</strong></span>
            <span>•</span>
            <span>Разработка компании: <strong>ИП MadiTech</strong></span>
          </div>

          <div class="prose">
            <p>
              Настоящая Политика конфиденциальности определяет порядок обработки и защиты персональной информации пользователей платформы <strong>MadiTech</strong> (далее — «Сервис», «Платформа»), доступной на домене <strong>loyalty.mevent.kz</strong>, разработка компании <strong>ИП MadiTech</strong>, включая интеграции с <strong>Google Wallet API</strong> (Google LLC), <strong>Apple PassKit</strong> (Apple Inc.), Telegram Mini App и кассовыми системами <strong>iiko Cloud</strong>.
            </p>

            <h2>1. Общие положения и оператор данных</h2>
            <p>
              Оператором персональных данных является компания <strong>ИП MadiTech</strong> (сервис MadiTech, сайт <strong>loyalty.mevent.kz</strong>).<br>
              <strong>Фактический и юридический адрес:</strong> Республика Казахстан, г. Актобе, проспект Абая 2/1.<br>
              <strong>Телефон службы поддержки:</strong> <a href="tel:+77779285899" class="accent-link">+7 777 9285899</a>.<br>
              <strong>Instagram:</strong> <a href="https://www.instagram.com/maditech_04" target="_blank" rel="noopener noreferrer" class="accent-link">@maditech_04</a>.<br>
              <strong>Официальный сайт:</strong> loyalty.mevent.kz
            </p>

            <h2>2. Какие данные мы собираем</h2>
            <p>
              В рамках предоставления сервиса электронных карт лояльности собираются только минимально необходимые данные:
            </p>
            <ul>
              <li><strong>Номер телефона:</strong> используется как основной идентификатор гостя в ресторанной системе iiko Cloud и для привязки карты в Google/Apple Wallet.</li>
              <li><strong>Имя и фамилия (по желанию):</strong> для персонализации обращения к гостю на лицевой стороне карты лояльности.</li>
              <li><strong>Дата рождения (по желанию):</strong> исключительно для автоматического начисления праздничных бонусов и поздравлений от заведения.</li>
              <li><strong>Баланс бонусов и номер карты:</strong> учет количества накопленных баллов и скидок в кассовой системе заведения.</li>
              <li><strong>Технические идентификаторы:</strong> обезличенные токены объектов Google Wallet Object ID и Apple PassKit Serial Number для доставки обновлений баланса на смартфон.</li>
            </ul>

            <h2>3. Цели сбора и использования информации</h2>
            <p>Персональные данные используются исключительно для следующих целей:</p>
            <ul>
              <li>Выпуск и отображение персональной карты лояльности в приложениях <strong>Google Wallet</strong> и <strong>Apple Wallet</strong>;</li>
              <li>Идентификация гостя при сканировании QR-кода карты на кассе ресторана (iiko);</li>
              <li>Отображение актуального баланса баллов и истории операций;</li>
              <li>Информирование гостя через Telegram/WhatsApp о начислении или сгорании бонусов (только при наличии согласия гостя);</li>
              <li>Техническая поддержка пользователей.</li>
            </ul>

            <h2>4. Передача данных третьим лицам</h2>
            <p>
              Сервис MadiTech <strong>ни при каких обстоятельствах не продает, не сдает в аренду и не передает</strong> персональные данные третьим лицам для рекламных целей.
            </p>
            <p>
              Данные передаются исключительно защищенным техническим партнерам, необходимым для функционирования сервиса:
            </p>
            <ul>
              <li><strong>Google LLC (Google Wallet API):</strong> для генерации ссылки сохранения карты и обновления баланса на устройствах Android;</li>
              <li><strong>Apple Inc. (Apple Developer / PassKit):</strong> для доставки файла .pkpass и Push-уведомлений на устройства iOS;</li>
              <li><strong>iiko Cloud (iiko Transport):</strong> кассовая учетная система ресторана для подтверждения прав на скидку или бонус.</li>
            </ul>

            <h2>5. Безопасность и хранение данных</h2>
            <p>
              Все данные передаются исключительно с использованием современных криптографических протоколов <strong>TLS 1.3 / HTTPS</strong>. Серверная инфраструктура защищена строгими политиками разграничения доступа, токены авторизации хранятся в зашифрованном виде.
            </p>

            <h2>6. Права пользователей и удаление данных</h2>
            <p>Каждый пользователь имеет право:</p>
            <ul>
              <li>Удалить сохраненную карту лояльности из Google Wallet или Apple Wallet в любой момент непосредственно на своем смартфоне;</li>
              <li>Запросить полное удаление своего аккаунта и связанных с ним данных из базы сервиса, позвонив или написав в службу поддержки по телефону <strong>+7 777 9285899</strong> или через Instagram <strong>@maditech_04</strong>. Данные удаляются в течение 48 часов с момента подтверждения заявки.</li>
            </ul>

            <h2>7. Изменения в Политике конфиденциальности</h2>
            <p>
              Мы оставляем за собой право вносить изменения в настоящую Политику при обновлении требований Google Wallet API, Apple PassKit или законодательства Республики Казахстан. Актуальная версия всегда доступна на странице <strong>https://loyalty.mevent.kz/privacy</strong>.
            </p>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="legal-footer">
      <div class="legal-container footer-row">
        <div>© 2026 loyalty.mevent.kz — Разработка компании ИП MadiTech. г. Актобе, пр. Абая 2/1. Телефон: +7 777 9285899.</div>
        <div class="footer-links">
          <router-link to="/">На главную</router-link>
          <router-link to="/privacy" class="active">Политика конфиденциальности</router-link>
          <router-link to="/terms">Пользовательское соглашение</router-link>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const dashboardUrl = computed(() => {
  if (!auth.isAuthenticated) return '/login'
  if (auth.isSuperAdmin) return '/superadmin'
  if (auth.currentOrgId) return '/admin/customers'
  return '/select-org'
})
</script>

<style scoped>
.legal-page {
  background-color: #08090E;
  color: #F8FAFC;
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  display: flex;
  flex-direction: column;
}

.legal-container {
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Header */
.legal-header {
  position: sticky;
  top: 0;
  height: 76px;
  background: rgba(8, 9, 14, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 50;
  display: flex;
  align-items: center;
}

.nav-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
}

.brand-logo-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366F1 0%, #06B6D4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.15rem;
  color: #FFFFFF;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.brand-logo-text {
  font-size: 1.35rem;
  font-weight: 800;
  color: #FFFFFF;
  letter-spacing: -0.02em;
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: 1.8rem;
}

.nav-item {
  color: #94A3B8;
  font-size: 0.92rem;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s ease;
}

.nav-item:hover {
  color: #FFFFFF;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  height: 40px;
  padding: 0 1.25rem;
  border-radius: 9999px;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.25s ease;
  white-space: nowrap;
  box-sizing: border-box;
}

.nav-btn-outline {
  background: rgba(255, 255, 255, 0.06);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.nav-btn-outline:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
}

.nav-btn-primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.nav-btn-primary:hover {
  background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
  transform: translateY(-1px);
}

/* Main */
.legal-main {
  flex: 1;
  padding: 3rem 0;
}

.legal-card {
  background: #111422;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
}

.breadcrumb {
  margin-bottom: 1.5rem;
}

.back-link {
  color: #818CF8;
  font-size: 0.9rem;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s;
}

.back-link:hover {
  color: #A5B4FC;
  text-decoration: underline;
}

.page-title {
  font-size: 2.2rem;
  font-weight: 800;
  color: #FFFFFF;
  margin-bottom: 1rem;
  line-height: 1.25;
}

.meta-badge {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  color: #94A3B8;
  font-size: 0.88rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 2rem;
}

.meta-badge strong {
  color: #E2E8F0;
}

/* Prose */
.prose {
  color: #CBD5E1;
  font-size: 1rem;
  line-height: 1.8;
}

.prose p {
  margin-bottom: 1.5rem;
}

.prose h2 {
  font-size: 1.35rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
  padding-left: 0.75rem;
  border-left: 3px solid #6366F1;
}

.prose ul {
  list-style: disc;
  padding-left: 1.5rem;
  margin-bottom: 1.5rem;
}

.prose li {
  margin-bottom: 0.5rem;
}

.accent-link {
  color: #818CF8;
  text-decoration: none;
  transition: color 0.2s;
}

.accent-link:hover {
  color: #A5B4FC;
  text-decoration: underline;
}

/* Footer */
.legal-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 2rem 0;
  background: #08090E;
  color: #64748B;
  font-size: 0.85rem;
}

.footer-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.footer-links {
  display: flex;
  gap: 1.5rem;
}

.footer-links a {
  color: #94A3B8;
  text-decoration: none;
  transition: color 0.2s;
}

.footer-links a:hover,
.footer-links a.active {
  color: #818CF8;
}

@media (max-width: 860px) {
  .nav-menu {
    display: none;
  }
  .legal-card {
    padding: 1.75rem;
  }
  .page-title {
    font-size: 1.75rem;
  }
  .footer-row {
    flex-direction: column;
    text-align: center;
  }
}
</style>
