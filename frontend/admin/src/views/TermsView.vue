<template>
  <div class="legal-page">
    <!-- Header / Navbar -->
    <header class="legal-header">
      <div class="legal-container nav-row">
        <router-link to="/" class="brand-logo">
          <div class="brand-logo-icon">M</div>
          <span class="brand-logo-text">Loyalty-MadiTech</span>
        </router-link>

        <nav class="nav-menu">
          <router-link to="/" class="nav-item">Главная</router-link>
          <router-link to="/#features" class="nav-item">Возможности</router-link>
          <router-link to="/#wallets" class="nav-item">Электронные кошельки</router-link>
          <router-link to="/privacy" class="nav-item">Политика конфиденциальности</router-link>
          <router-link to="/#contacts" class="nav-item">Контакты</router-link>
        </nav>

        <div class="nav-actions">
          <router-link :to="dashboardUrl" class="nav-btn nav-btn-outline" id="btn-terms-login">
            <span>{{ auth.isAuthenticated ? 'В панель' : 'Войти' }}</span>
          </router-link>
          <a
            href="https://wa.me/77779285899?text=Здравствуйте!%20Хочу%20подключить%20Loyalty-MadiTech"
            target="_blank"
            rel="noopener noreferrer"
            class="nav-btn nav-btn-primary"
            id="btn-terms-connect"
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

          <h1 class="page-title">Пользовательское соглашение (Terms of Service)</h1>
          <div class="meta-badge">
            <span>Дата публикации: 1 января 2026 г.</span>
            <span>•</span>
            <span>Домен: <strong>loyalty.mevent.kz</strong></span>
            <span>•</span>
            <span>Разработка компании: <strong>ИП MadiTech</strong></span>
          </div>

          <div class="prose">
            <p>
              Настоящее Пользовательское соглашение (далее — «Соглашение») регулирует отношения между компанией <strong>ИП MadiTech</strong> (далее — «Администрация», «Сервис», веб-сайт <strong>loyalty.mevent.kz</strong>) и пользователем (далее — «Пользователь», «Гость»), возникающие при использовании платформы на сайте <strong>loyalty.mevent.kz</strong>, в Telegram Mini App, а также при сохранении цифровых карт в приложениях <strong>Google Wallet</strong> и <strong>Apple Wallet</strong>.
            </p>

            <h2>1. О сервисе и предмет соглашения</h2>
            <p>
              Платформа разработана компанией <strong>ИП MadiTech</strong> и предоставляет программное обеспечение для автоматизации программ лояльности заведений общественного питания (ресторанов, кафе, баров). Сервис позволяет гостям выпускать электронные бонусные карты, сохранять их в Google Wallet / Apple Wallet, проверять баланс бонусов и получать привилегии на кассах заведений, использующих учетную систему iiko.
            </p>

            <h2>2. Выпуск и использование цифровых карт</h2>
            <ul>
              <li>Цифровая карта выпускается бесплатно по запросу гостя после подтверждения номера телефона.</li>
              <li>Для использования карты гость предъявляет отображаемый в Google Wallet, Apple Wallet или Telegram Mini App QR-код сотруднику заведения на кассе.</li>
              <li>Начисление и списание баллов осуществляется по правилам конкретного заведения-эмитента программы лояльности, настроенным в учетной системе iiko.</li>
              <li>Карта является персональной и не подлежит продаже или возмездному отчуждению.</li>
            </ul>

            <h2>3. Взаимодействие с сервисами Google Wallet и Apple Wallet</h2>
            <ul>
              <li>Использование Google Wallet регулируется Условиями использования Google Pay / Wallet (Google LLC).</li>
              <li>Использование Apple Wallet регулируется Условиями обслуживания Apple Inc. и политикой использования iOS PassKit.</li>
              <li>MadiTech гарантирует актуальность передачи баланса бонусов и номера карты в Google Wallet и Apple Wallet при наличии стабильного интернет-соединения на устройстве пользователя.</li>
            </ul>

            <h2>4. Ограничение ответственности</h2>
            <ul>
              <li>Администрация сервиса предпринимает все разумные меры для обеспечения бесперебойной работы платформы, однако не несет ответственности за временные сбои на стороне операторов связи, кассовых систем сторонних заведений или глобальных сервисов Apple и Google.</li>
              <li>Правила предоставления скидок, размеры бонусов и сроки их действия определяются администрацией конкретного ресторана-партнера.</li>
            </ul>

            <h2>5. Интеллектуальная собственность</h2>
            <p>
              Все элементы платформы MadiTech (дизайн, программный код, базы данных, товарные знаки) являются интеллектуальной собственностью компании <strong>ИП MadiTech</strong> и охраняются законодательством об авторском праве.
            </p>

            <h2>6. Контактные данные и поддержка</h2>
            <p>По всем вопросам, предложениям и претензиям, касающимся работы сервиса:</p>
            <p>
              <strong>Разработчик и оператор:</strong> ИП MadiTech<br>
              <strong>Веб-сайт:</strong> loyalty.mevent.kz<br>
              <strong>Адрес:</strong> Республика Казахстан, г. Актобе, проспект Абая 2/1<br>
              <strong>Телефон поддержки:</strong> <a href="tel:+77779285899" class="accent-link">+7 777 9285899</a><br>
              <strong>Instagram:</strong> <a href="https://www.instagram.com/maditech_04" target="_blank" rel="noopener noreferrer" class="accent-link">@maditech_04</a>
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
          <router-link to="/privacy">Политика конфиденциальности</router-link>
          <router-link to="/terms" class="active">Пользовательское соглашение</router-link>
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
  .legal-header {
    height: 64px;
  }
  .brand-logo-icon {
    width: 32px;
    height: 32px;
    font-size: 0.95rem;
  }
  .brand-logo-text {
    font-size: 1.15rem;
    white-space: nowrap;
  }
  .nav-menu {
    display: none;
  }
  .nav-btn {
    height: 36px;
    padding: 0 0.85rem;
    font-size: 0.82rem;
  }
  .legal-card {
    padding: 1.5rem;
  }
  .page-title {
    font-size: 1.65rem;
  }
  .footer-row {
    flex-direction: column;
    text-align: center;
  }
}
</style>
