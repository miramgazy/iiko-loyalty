<template>
  <div class="landing-page">
    <!-- ================= NAVBAR ================= -->
    <header class="landing-header">
      <div class="landing-container nav-row">
        <!-- Logo -->
        <router-link to="/" class="brand-logo">
          <div class="brand-logo-icon">M</div>
          <span class="brand-logo-text">Loyalty-MadiTech</span>
        </router-link>

        <!-- Nav Links (Desktop) -->
        <nav class="nav-menu">
          <a href="#features" class="nav-item">Возможности</a>
          <a href="#wallets" class="nav-item">Электронные кошельки</a>
          <a href="#iiko" class="nav-item">Интеграция с iiko</a>
          <a href="#compliance" class="nav-item">Google & Apple</a>
          <a href="#contacts" class="nav-item">Контакты</a>
        </nav>

        <!-- Nav Actions (Desktop uniform buttons + Mobile animated hamburger) -->
        <div class="nav-actions">
          <router-link :to="dashboardUrl" class="nav-btn nav-btn-outline" id="btn-header-login">
            <span>{{ auth.isAuthenticated ? 'В панель' : 'Войти' }}</span>
          </router-link>

          <a
            href="https://wa.me/77779285899?text=Здравствуйте!%20Хочу%20подключить%20Loyalty-MadiTech"
            target="_blank"
            rel="noopener noreferrer"
            class="nav-btn nav-btn-primary"
            id="btn-header-connect"
          >
            <span>Подключить</span>
          </a>

          <!-- Mobile Hamburger Button (Animated 3-bar) -->
          <button
            @click="mobileMenuOpen = !mobileMenuOpen"
            class="mobile-toggle-btn"
            :class="{ 'is-active': mobileMenuOpen }"
            aria-label="Меню"
            id="btn-mobile-hamburger"
          >
            <span class="bar bar-1"></span>
            <span class="bar bar-2"></span>
            <span class="bar bar-3"></span>
          </button>
        </div>
      </div>

      <!-- Backdrop overlay -->
      <transition name="fade">
        <div v-if="mobileMenuOpen" class="mobile-backdrop" @click="mobileMenuOpen = false"></div>
      </transition>

      <!-- Mobile Dropdown Menu -->
      <transition name="mobile-menu-anim">
        <div v-if="mobileMenuOpen" class="mobile-dropdown">
          <nav class="mobile-nav-list">
            <a href="#features" @click="mobileMenuOpen = false" class="mobile-nav-link">
              <span class="mobile-nav-link-title">🚀 Возможности платформы</span>
              <span class="mobile-nav-link-arrow">→</span>
            </a>
            <a href="#wallets" @click="mobileMenuOpen = false" class="mobile-nav-link">
              <span class="mobile-nav-link-title">💳 Электронные кошельки</span>
              <span class="mobile-nav-link-arrow">→</span>
            </a>
            <a href="#iiko" @click="mobileMenuOpen = false" class="mobile-nav-link">
              <span class="mobile-nav-link-title">⚡️ Интеграция с iiko</span>
              <span class="mobile-nav-link-arrow">→</span>
            </a>
            <a href="#compliance" @click="mobileMenuOpen = false" class="mobile-nav-link">
              <span class="mobile-nav-link-title">🛡️ Google & Apple стандарты</span>
              <span class="mobile-nav-link-arrow">→</span>
            </a>
            <a href="#contacts" @click="mobileMenuOpen = false" class="mobile-nav-link">
              <span class="mobile-nav-link-title">📞 Контакты и поддержка</span>
              <span class="mobile-nav-link-arrow">→</span>
            </a>
          </nav>

          <div class="mobile-nav-divider"></div>

          <div class="mobile-actions-group">
            <router-link
              :to="dashboardUrl"
              @click="mobileMenuOpen = false"
              class="mobile-nav-btn mobile-nav-btn-login"
            >
              <span>{{ auth.isAuthenticated ? 'В панель управления' : 'Войти в панель' }}</span>
            </router-link>
            <a
              href="https://wa.me/77779285899?text=Здравствуйте!%20Хочу%20подключить%20Loyalty-MadiTech"
              target="_blank"
              class="mobile-nav-btn mobile-nav-btn-primary"
            >
              <span>Подключить ресторан</span>
            </a>
          </div>

          <div class="mobile-drawer-contacts">
            <a href="tel:+77779285899" class="drawer-contact-item">
              <span>📞 +7 777 9285899</span>
            </a>
            <a href="https://www.instagram.com/maditech_04" target="_blank" rel="noopener noreferrer" class="drawer-contact-item">
              <span>📸 @maditech_04</span>
            </a>
          </div>
        </div>
      </transition>
    </header>

    <!-- ================= HERO SECTION ================= -->
    <section class="hero-section" id="home">
      <div class="landing-container hero-grid">
        <!-- Hero Text -->
        <div class="hero-left">
          <div class="hero-badge">
            <span class="hero-badge-pulse"></span>
            <span>Google Wallet, Apple Wallet & Telegram Mini App</span>
          </div>

          <h1 class="hero-title">
            Экосистема лояльности нового поколения для <span class="gradient-text">ресторанов и кафе</span>
          </h1>

          <p class="hero-desc">
            <strong>Loyalty-MadiTech</strong> — облачная платформа автоматизации лояльности. Выпускайте брендированные карты в <strong>Google Wallet</strong> и <strong>Apple Wallet</strong>, запускайте <strong>Telegram Mini App</strong> и управляйте бонусами гостей через прямую синхронизацию с кассами <strong>iiko Cloud</strong>.
          </p>

          <div class="hero-actions-row">
            <a
              href="https://wa.me/77779285899?text=Здравствуйте!%20Хочу%20подключить%20Loyalty-MadiTech"
              target="_blank"
              class="hero-cta-btn hero-cta-primary"
            >
              <span>💬 Запросить демонстрацию</span>
            </a>
            <router-link to="/login" class="hero-cta-btn hero-cta-secondary">
              <span>Войти в систему →</span>
            </router-link>
          </div>

          <div class="hero-stats-row">
            <div class="stat-cell">
              <h3>1 клик</h3>
              <p>добавление карты в смартфон</p>
            </div>
            <div class="stat-cell">
              <h3>100%</h3>
              <p>синхронизация с кассой iiko</p>
            </div>
            <div class="stat-cell">
              <h3>+35%</h3>
              <p>рост повторных визитов</p>
            </div>
          </div>
        </div>

        <!-- Hero Showcase: Interactive Smartphone Frame -->
        <div class="hero-right">
          <!-- Switch Tabs -->
          <div class="card-switcher">
            <button
              @click="activeMode = 'google'"
              class="card-switch-tab"
              :class="{ active: activeMode === 'google' }"
              data-mode="google"
            >
              <span class="tab-emoji"></span> Google Wallet
            </button>
            <button
              @click="activeMode = 'apple'"
              class="card-switch-tab"
              :class="{ active: activeMode === 'apple' }"
              data-mode="apple"
            >
              <span class="tab-emoji"></span> Apple Wallet
            </button>
            <button
              @click="activeMode = 'tma'"
              class="card-switch-tab"
              :class="{ active: activeMode === 'tma' }"
              data-mode="tma"
            >
              <span class="tab-emoji"></span> Telegram Mini App
            </button>
          </div>

          <!-- Smartphone Mockup -->
          <div class="phone-mockup-wrapper">
            <div
              class="phone-chassis"
              :class="`glow-${activeMode}`"
              @click="cycleMode"
              title="Нажмите для переключения карты"
            >
              <!-- Dynamic Island -->
              <div class="phone-island">
                <span class="island-camera"></span>
                <span class="island-speaker"></span>
              </div>

              <!-- Screen -->
              <div class="phone-screen">
                <img
                  src="/image/GoogleWallet.jpeg"
                  alt="Google Wallet Pass"
                  class="screen-image"
                  :class="{ active: activeMode === 'google' }"
                  id="img-google"
                />
                <img
                  src="/image/AppleWallet.jpeg"
                  alt="Apple Wallet Pass"
                  class="screen-image"
                  :class="{ active: activeMode === 'apple' }"
                  id="img-apple"
                />
                <img
                  src="/image/TMA.jpeg"
                  alt="Telegram Mini App"
                  class="screen-image"
                  :class="{ active: activeMode === 'tma' }"
                  id="img-tma"
                />
              </div>

              <!-- Glare & Home Indicator -->
              <div class="phone-glare"></div>
              <div class="phone-indicator"></div>
            </div>

            <!-- Meta Caption -->
            <div class="phone-meta">
              <span class="meta-badge-pill">{{ badgeLabels[activeMode] }}</span>
              <span class="meta-hint">✨ Нажмите на экран смартфона для быстрой смены</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= FEATURES SECTION ================= -->
    <section class="landing-section" id="features">
      <div class="landing-container">
        <div class="section-heading">
          <span class="section-tag">Преимущества платформы</span>
          <h2 class="section-title">Всё для лояльности гостей в одном решении</h2>
          <p class="section-desc">
            Забудьте о дорогих мобильных приложениях, которые никто не хочет скачивать. Loyalty-MadiTech дает ресторанам готовые инструменты прямо в телефонах гостей.
          </p>
        </div>

        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">💳</div>
            <h3 class="feature-card-title">Электронные кошельки Wallet</h3>
            <p class="feature-card-desc">
              Карта всегда под рукой в Apple Wallet или Google Кошельке. Без необходимости ставить сторонние приложения из App Store или Google Play.
            </p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">📲</div>
            <h3 class="feature-card-title">Telegram Mini App (TMA)</h3>
            <p class="feature-card-desc">
              Полноценный личный кабинет гостя внутри Telegram: моментальная регистрация по номеру телефона.
            </p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3 class="feature-card-title">Бесшовная интеграция с iiko</h3>
            <p class="feature-card-desc">
              Прямая синхронизация с кассами через iiko Transport API. Бонусы начисляются и списываются мгновенно при сканировании QR-кода на кассе.
            </p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-card-title">Аналитика и сегментация гостей</h3>
            <p class="feature-card-desc">
              Удобная панель управления для управляющих: статистика повторных визитов и целевые рассылки.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= WALLETS & IIKO INTEGRATION ================= -->
    <section class="landing-section bg-alt" id="wallets">
      <div class="landing-container">
        <div class="integration-banner">
          <div class="integration-left">
            <span class="section-tag">Кассовая синхронизация</span>
            <h2 class="section-title" style="text-align: left; margin: 0.5rem 0 1rem;">
              Прямая работа с кассами iiko Cloud
            </h2>
            <p class="section-desc" style="text-align: left; margin: 0 0 1.5rem;">
              После закрытия чека на кассе баланс на карточке в Google и Apple Wallet обновляется автоматически прямо на экране смартфона гостя.
            </p>

            <ul class="check-list">
              <li>
                <span class="check-mark">✓</span>
                <div>
                  <strong>Google Wallet API (Passes REST API)</strong>
                  <p>Официальные партнерские классы лояльности с брендированным баннером и пушами.</p>
                </div>
              </li>
              <li>
                <span class="check-mark">✓</span>
                <div>
                  <strong>Apple Wallet PassKit</strong>
                  <p>Криптографическая подпись сертификатом Apple Pass Type ID и обновление через APNs.</p>
                </div>
              </li>
              <li>
                <span class="check-mark">✓</span>
                <div>
                  <strong>iiko Cloud Transport & iikoCard</strong>
                  <p>Двусторонняя передача данных о клиентах, виртуальных картах и балансах бонусных кошельков.</p>
                </div>
              </li>
            </ul>

            <div class="tech-chips">
              <span class="tech-chip">Android Ready</span>
              <span class="tech-chip">iOS PassKit Ready</span>
              <span class="tech-chip">iiko Transport API v1</span>
              <span class="tech-chip">Telegram WebApp</span>
            </div>
          </div>

          <div class="integration-right">
            <h3 class="steps-box-title">Как это работает для вашего гостя:</h3>
            <div class="steps-flow">
              <div class="step-card">
                <span class="step-num">01</span>
                <div>
                  <h4>Сканирование QR на столике</h4>
                  <p>Гость наводит камеру смартфона на QR-код и подтверждает номер телефона в 1 клик.</p>
                </div>
              </div>
              <div class="step-card">
                <span class="step-num">02</span>
                <div>
                  <h4>Добавление в кошелек телефона</h4>
                  <p>Карта мгновенно добавляется в Google Wallet (Android) или Apple Wallet (iPhone).</p>
                </div>
              </div>
              <div class="step-card">
                <span class="step-num">03</span>
                <div>
                  <h4>Сканирование на кассе iiko</h4>
                  <p>Официант или кассир считывает QR сканером — скидка или бонусы применяются мгновенно.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= COMPLIANCE & SECURITY ================= -->
    <section class="landing-section" id="compliance">
      <div class="landing-container">
        <div class="section-heading">
          <span class="section-tag">Безопасность и соответствие</span>
          <h2 class="section-title">Соответствие стандартам Google и Apple</h2>
          <p class="section-desc">
            Сервис <strong>Loyalty-MadiTech</strong> (домен <strong>loyalty.mevent.kz</strong>, разработка компании <strong>ИП MadiTech</strong>) строго следует политикам безопасности Google API Services User Data Policy и руководству Apple Developer PassKit Guidelines.
          </p>
        </div>

        <div class="compliance-cards-row">
          <div class="compliance-card">
            <div class="compliance-header">
              <span class="compliance-emoji">🛡️</span>
              <div>
                <h3>Защита данных и конфиденциальность</h3>
                <span class="compliance-tag">Google & Apple Verified</span>
              </div>
            </div>
            <p>
              Мы используем протокол шифрования TLS 1.3 / HTTPS для всех сетевых взаимодействий. Данные клиентов ресторанов используются исключительно для выпуска электронных карт лояльности и начисления бонусов. Мы <strong>никогда не продаем и не передаем</strong> пользовательские данные сторонним рекламным сетям.
            </p>
            <div class="compliance-action">
              <router-link to="/privacy" class="compliance-btn">
                <span>📄 Политика конфиденциальности (Privacy Policy) →</span>
              </router-link>
            </div>
          </div>

          <div class="compliance-card">
            <div class="compliance-header">
              <span class="compliance-emoji">📜</span>
              <div>
                <h3>Условия обслуживания и эмитент карт</h3>
                <span class="compliance-tag">SaaS Platform</span>
              </div>
            </div>
            <p>
              Сервис <strong>Loyalty-MadiTech</strong> разработан компанией ИП MadiTech и выступает сертифицированным технологическим провайдером (Service Provider) для заведений общественного питания. Каждый ресторан является официальным эмитентом собственной программы лояльности, а <strong>Loyalty-MadiTech</strong> обеспечивает безопасный выпуск и криптографическую подпись цифровых карт.
            </p>
            <div class="compliance-action">
              <router-link to="/terms" class="compliance-btn">
                <span>⚖️ Пользовательское соглашение (Terms of Service) →</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= CONTACTS & REQUISITES ================= -->
    <section class="landing-section bg-alt" id="contacts">
      <div class="landing-container">
        <div class="section-heading">
          <span class="section-tag">Связь и поддержка</span>
          <h2 class="section-title">Контакты и служба поддержки</h2>
          <p class="section-desc">
            Мы всегда на связи с нашими партнерами и гостями. По всем вопросам подключения заведений и работы электронных карт обращайтесь в нашу службу поддержки.
          </p>
        </div>

        <div class="contacts-wrapper">
          <!-- Details -->
          <div class="contacts-card">
            <h3 class="contacts-box-title">Реквизиты и контакты MadiTech</h3>

            <div class="contact-row">
              <div class="contact-icon">📞</div>
              <div>
                <div class="contact-label">Телефон поддержки / WhatsApp</div>
                <div class="contact-val">
                  <a href="tel:+77779285899">+7 777 9285899</a>
                </div>
                <div class="contact-sub">Пн-Вс: 09:00 – 21:00 (время Астаны)</div>
              </div>
            </div>

            <div class="contact-row">
              <div class="contact-icon">📍</div>
              <div>
                <div class="contact-label">Фактический и юридический адрес</div>
                <div class="contact-val">Республика Казахстан, г. Актобе, проспект Абая 2/1</div>
                <div class="contact-sub">Почтовый индекс: 030000</div>
              </div>
            </div>

            <div class="contact-row">
              <div class="contact-icon">📷</div>
              <div>
                <div class="contact-label">Официальный Instagram</div>
                <div class="contact-val">
                  <a href="https://www.instagram.com/maditech_04" target="_blank" rel="noopener noreferrer">@maditech_04</a>
                </div>
                <div class="contact-sub">Следите за обновлениями и новыми кейсами</div>
              </div>
            </div>

            <div class="contact-row" style="margin-bottom: 0;">
              <div class="contact-icon">🌐</div>
              <div>
                <div class="contact-label">Основной домен сервиса</div>
                <div class="contact-val">loyalty.mevent.kz</div>
                <div class="contact-sub">Разработка компании ИП MadiTech</div>
              </div>
            </div>
          </div>

          <!-- Quick Connect -->
          <div class="contacts-card cta-box">
            <div>
              <h3 class="contacts-box-title">Готовы подключить ваше заведение?</h3>
              <p class="cta-box-desc">
                Мы настроим интеграцию с вашей кассой iiko, подготовим фирменный дизайн карт в Google Wallet и Apple Wallet и запустим Telegram Mini App за 1–2 рабочих дня.
              </p>

              <ul class="cta-benefits">
                <li><span class="text-emerald-400">✓</span> Бесплатная демонстрация возможностей</li>
                <li><span class="text-emerald-400">✓</span> Подключение под ключ и обучение персонала</li>
                <li><span class="text-emerald-400">✓</span> Круглосуточная техническая поддержка</li>
              </ul>
            </div>

            <div class="cta-btns">
              <a
                href="https://wa.me/77779285899?text=Здравствуйте!%20Хочу%20подключить%20Loyalty-MadiTech"
                target="_blank"
                class="cta-btn cta-btn-primary"
              >
                <span>Написать в WhatsApp</span>
              </a>
              <a
                href="https://www.instagram.com/maditech_04"
                target="_blank"
                class="cta-btn cta-btn-secondary"
              >
                <span>Перейти в Instagram @maditech_04</span>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ================= FOOTER ================= -->
    <footer class="landing-footer">
      <div class="landing-container">
        <div class="footer-grid">
          <div>
            <div class="brand-logo">
              <div class="brand-logo-icon">M</div>
              <span class="brand-logo-text">Loyalty-MadiTech</span>
            </div>
            <p class="footer-about">
              Современная платформа цифровой лояльности для ресторанов и сферы гостеприимства. Электронные кошельки, Telegram Mini App и iiko Cloud. Разработка компании <strong>ИП MadiTech</strong>.
            </p>
            <div class="footer-domain-tag">
              Домен: <strong>loyalty.mevent.kz</strong> • Разработка компании <strong>ИП MadiTech</strong>
            </div>
          </div>

          <div>
            <h4 class="footer-title">Платформа</h4>
            <ul class="footer-links">
              <li><a href="#features">Возможности</a></li>
              <li><a href="#wallets">Google & Apple Wallet</a></li>
              <li><a href="#iiko">Интеграция с iiko</a></li>
              <li><a href="#compliance">Безопасность данных</a></li>
            </ul>
          </div>

          <div>
            <h4 class="footer-title">Правовая информация</h4>
            <ul class="footer-links">
              <li><router-link to="/privacy">Политика конфиденциальности</router-link></li>
              <li><router-link to="/terms">Пользовательское соглашение</router-link></li>
              <li><a href="#contacts">Контакты службы поддержки</a></li>
            </ul>
          </div>
        </div>

        <div class="footer-bottom-bar">
          <div>
            © 2026 loyalty.mevent.kz — Разработка компании ИП MadiTech. Все права защищены. г. Актобе, пр. Абая 2/1.
          </div>
          <div class="footer-legal-links">
            <router-link to="/privacy">Privacy Policy</router-link>
            <router-link to="/terms">Terms of Service</router-link>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const mobileMenuOpen = ref(false)
const activeMode = ref('google')

const dashboardUrl = computed(() => {
  if (!auth.isAuthenticated) return '/login'
  if (auth.isSuperAdmin) return '/superadmin'
  if (auth.currentOrgId) return '/admin/customers'
  return '/select-org'
})

const modes = ['google', 'apple', 'tma']
const badgeLabels = {
  google: 'Google Wallet Pass • Android',
  apple: 'Apple Wallet PassKit • iOS',
  tma: 'Telegram Mini App • Все платформы'
}

function cycleMode() {
  const currentIndex = modes.indexOf(activeMode.value)
  const nextIndex = (currentIndex + 1) % modes.length
  activeMode.value = modes[nextIndex]
}
</script>

<style scoped>
/* Page Layout */
.landing-page {
  background-color: #08090E;
  color: #F8FAFC;
  min-height: 100vh;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow-x: hidden;
}

.landing-container {
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Header & Navbar */
.landing-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 76px;
  background: rgba(8, 9, 14, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 100;
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

/* Nav Actions (Uniform) */
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
  cursor: pointer;
}

.nav-btn-outline {
  background: rgba(255, 255, 255, 0.06);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(10px);
}

.nav-btn-outline:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
}

.nav-btn-primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  border: 1px solid transparent;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.nav-btn-primary:hover {
  background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

/* Animated Hamburger Button */
.mobile-toggle-btn {
  display: none;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 12px;
  width: 42px;
  height: 42px;
  cursor: pointer;
  padding: 0;
  position: relative;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 5px;
  transition: all 0.25s ease;
  backdrop-filter: blur(8px);
}

.mobile-toggle-btn:active {
  transform: scale(0.92);
  background: rgba(255, 255, 255, 0.12);
}

.mobile-toggle-btn .bar {
  display: block;
  width: 20px;
  height: 2px;
  background: #FFFFFF;
  border-radius: 2px;
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.mobile-toggle-btn.is-active .bar-1 {
  transform: translateY(7px) rotate(45deg);
}

.mobile-toggle-btn.is-active .bar-2 {
  opacity: 0;
  transform: scaleX(0);
}

.mobile-toggle-btn.is-active .bar-3 {
  transform: translateY(-7px) rotate(-45deg);
}

/* Mobile Backdrop */
.mobile-backdrop {
  position: fixed;
  top: 76px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  z-index: 95;
}

/* Mobile Dropdown Menu Drawer */
.mobile-dropdown {
  position: absolute;
  top: 76px;
  left: 0;
  right: 0;
  background: rgba(10, 12, 18, 0.98);
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  padding: 1.25rem 1.25rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
  z-index: 100;
  max-height: calc(100vh - 76px);
  overflow-y: auto;
}

.mobile-nav-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.mobile-nav-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #E2E8F0;
  font-size: 0.95rem;
  font-weight: 500;
  text-decoration: none;
  padding: 0.75rem 0.85rem;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.mobile-nav-link:hover,
.mobile-nav-link:active {
  background: rgba(255, 255, 255, 0.08);
  color: #FFFFFF;
}

.mobile-nav-link-arrow {
  color: #64748B;
  font-size: 0.85rem;
  transition: transform 0.2s ease;
}

.mobile-nav-link:hover .mobile-nav-link-arrow {
  transform: translateX(3px);
  color: #818CF8;
}

.mobile-nav-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.08);
  margin: 0;
}

.mobile-actions-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.mobile-nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 46px;
  padding: 0 1rem;
  border-radius: 12px;
  font-size: 0.92rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
}

.mobile-nav-btn-login {
  background: rgba(255, 255, 255, 0.06);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.mobile-nav-btn-login:active {
  background: rgba(255, 255, 255, 0.12);
}

.mobile-nav-btn-primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.mobile-drawer-contacts {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.drawer-contact-item {
  color: #94A3B8;
  font-size: 0.85rem;
  text-decoration: none;
  transition: color 0.2s ease;
}

.drawer-contact-item:hover {
  color: #818CF8;
}

/* Mobile Menu Transitions */
.mobile-menu-anim-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.mobile-menu-anim-leave-active {
  transition: all 0.2s ease-in;
}
.mobile-menu-anim-enter-from,
.mobile-menu-anim-leave-to {
  transform: translateY(-16px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Hero Section */
.hero-section {
  padding: 150px 0 90px;
  position: relative;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  align-items: center;
  gap: 3.5rem;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 1rem;
  border-radius: 9999px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #818CF8;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.hero-badge-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10B981;
  box-shadow: 0 0 10px #10B981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

.hero-title {
  font-size: 3.25rem;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin-bottom: 1.5rem;
  color: #FFFFFF;
}

.gradient-text {
  background: linear-gradient(135deg, #FFFFFF 30%, #818CF8 75%, #06B6D4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-desc {
  font-size: 1.12rem;
  color: #94A3B8;
  line-height: 1.7;
  margin-bottom: 2.2rem;
  max-width: 580px;
}

.hero-actions-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 3rem;
  flex-wrap: wrap;
}

.hero-cta-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.85rem 1.6rem;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 9999px;
  text-decoration: none;
  transition: all 0.25s ease;
}

.hero-cta-primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 20px -2px rgba(99, 102, 241, 0.5);
}

.hero-cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(99, 102, 241, 0.6);
}

.hero-cta-secondary {
  background: rgba(255, 255, 255, 0.06);
  color: #F8FAFC;
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
}

.hero-cta-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.hero-stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-cell h3 {
  font-size: 1.8rem;
  font-weight: 800;
  color: #FFFFFF;
  margin-bottom: 0.2rem;
}

.stat-cell p {
  font-size: 0.82rem;
  color: #64748B;
  line-height: 1.4;
}

/* Smartphone Showcase */
.hero-right {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.card-switcher {
  display: inline-flex;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
  padding: 5px;
  margin-bottom: 1.8rem;
  backdrop-filter: blur(12px);
  gap: 4px;
}

.card-switch-tab {
  padding: 8px 16px;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 600;
  background: transparent;
  color: #94A3B8;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.25s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  white-space: nowrap;
}

.tab-emoji {
  font-size: 0.95rem;
}

.card-switch-tab:hover {
  color: #FFFFFF;
  background: rgba(255, 255, 255, 0.05);
}

.card-switch-tab.active[data-mode="google"] {
  background: linear-gradient(135deg, #4285F4 0%, #1A73E8 100%);
  color: #FFFFFF;
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 15px rgba(66, 133, 244, 0.45);
}

.card-switch-tab.active[data-mode="apple"] {
  background: linear-gradient(135deg, #D92365 0%, #9D174D 100%);
  color: #FFFFFF;
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 15px rgba(217, 35, 101, 0.45);
}

.card-switch-tab.active[data-mode="tma"] {
  background: linear-gradient(135deg, #0088CC 0%, #2AABEE 100%);
  color: #FFFFFF;
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 15px rgba(42, 171, 238, 0.45);
}

.phone-mockup-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  width: 100%;
}

.phone-chassis {
  width: 310px;
  height: 620px;
  border-radius: 46px;
  background: linear-gradient(145deg, #282A38 0%, #11121C 100%);
  border: 3px solid #36394E;
  position: relative;
  padding: 10px;
  cursor: pointer;
  transition: transform 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.4s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.4s ease;
  user-select: none;
}

.phone-chassis:hover {
  transform: translateY(-8px) scale(1.015);
}

.phone-chassis.glow-google {
  box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.85), 0 0 50px -10px rgba(66, 133, 244, 0.4);
  border-color: rgba(66, 133, 244, 0.45);
}

.phone-chassis.glow-apple {
  box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.85), 0 0 50px -10px rgba(217, 35, 101, 0.4);
  border-color: rgba(217, 35, 101, 0.45);
}

.phone-chassis.glow-tma {
  box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.85), 0 0 50px -10px rgba(42, 171, 238, 0.4);
  border-color: rgba(42, 171, 238, 0.45);
}

.phone-island {
  position: absolute;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  width: 86px;
  height: 22px;
  background: #000000;
  border-radius: 14px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 14px;
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.island-camera {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #0A0A14;
  border: 1.5px solid #1A1B2A;
  margin-right: 6px;
  box-shadow: inset 0 0 2px #3B82F6;
}

.island-speaker {
  width: 24px;
  height: 3px;
  border-radius: 2px;
  background: #181926;
}

.phone-screen {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 36px;
  overflow: hidden;
  background: #000000;
}

.screen-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  transform: scale(0.96) translateY(6px);
  transition: opacity 0.35s cubic-bezier(0.4, 0, 0.2, 1), transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  user-select: none;
}

.screen-image.active {
  opacity: 1;
  transform: scale(1) translateY(0);
  pointer-events: auto;
}

#img-google {
  object-fit: cover;
  object-position: top center;
  background: #202124;
}

#img-apple {
  object-fit: contain;
  object-position: center;
  background: #0B0C13;
  padding: 16px 6px;
}

#img-tma {
  object-fit: cover;
  object-position: top center;
  background: #000000;
}

.phone-glare {
  position: absolute;
  inset: 10px;
  border-radius: 36px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.02) 40%, transparent 60%);
  pointer-events: none;
  z-index: 5;
}

.phone-indicator {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  width: 110px;
  height: 4px;
  background: rgba(255, 255, 255, 0.45);
  border-radius: 4px;
  z-index: 10;
  pointer-events: none;
}

.phone-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
}

.meta-badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 6px 14px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.07);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 0.8rem;
  font-weight: 600;
  color: #FFFFFF;
  transition: all 0.3s ease;
}

.meta-hint {
  font-size: 0.75rem;
  color: #64748B;
}

/* Landing Section */
.landing-section {
  padding: 100px 0;
  position: relative;
}

.bg-alt {
  background: rgba(14, 17, 27, 0.5);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.section-heading {
  text-align: center;
  max-width: 680px;
  margin: 0 auto 3.5rem;
}

.section-tag {
  display: inline-block;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #818CF8;
  margin-bottom: 0.8rem;
}

.section-title {
  font-size: 2.35rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #FFFFFF;
  margin-bottom: 1rem;
}

.section-desc {
  font-size: 1.05rem;
  color: #94A3B8;
  line-height: 1.6;
}

/* Features Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
}

.feature-card {
  background: rgba(18, 20, 32, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 2rem;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.feature-card:hover {
  transform: translateY(-5px);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 15px 35px -10px rgba(99, 102, 241, 0.15);
}

.feature-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.feature-card-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 0.75rem;
}

.feature-card-desc {
  font-size: 0.92rem;
  color: #94A3B8;
  line-height: 1.6;
}

/* Integration Section */
.integration-banner {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 3rem;
  align-items: center;
}

.check-list {
  list-style: none;
  padding: 0;
  margin: 0 0 2rem 0;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.check-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
}

.check-mark {
  color: #10B981;
  font-weight: 800;
  font-size: 1.1rem;
  line-height: 1.2;
}

.check-list strong {
  display: block;
  color: #FFFFFF;
  font-size: 0.95rem;
  margin-bottom: 0.2rem;
}

.check-list p {
  color: #94A3B8;
  font-size: 0.88rem;
  line-height: 1.5;
  margin: 0;
}

.tech-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.tech-chip {
  padding: 6px 12px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.8rem;
  color: #CBD5E1;
  font-weight: 500;
}

.integration-right {
  background: rgba(8, 9, 14, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 2.2rem;
}

.steps-box-title {
  font-size: 1.3rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 1.5rem;
}

.steps-flow {
  display: flex;
  flex-direction: column;
  gap: 1.3rem;
}

.step-card {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.step-num {
  font-size: 1.2rem;
  font-weight: 800;
  color: #818CF8;
}

.step-card h4 {
  color: #FFFFFF;
  font-size: 0.95rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.step-card p {
  color: #94A3B8;
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0;
}

/* Compliance Section */
.compliance-cards-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.compliance-card {
  background: rgba(18, 20, 32, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 2.2rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.compliance-header {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  margin-bottom: 1.2rem;
}

.compliance-emoji {
  font-size: 2rem;
}

.compliance-header h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 0.25rem;
}

.compliance-tag {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 9999px;
  background: rgba(16, 185, 129, 0.15);
  color: #10B981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.compliance-card p {
  color: #94A3B8;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.compliance-btn {
  font-size: 0.88rem;
  color: #818CF8;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.28);
  padding: 8px 16px;
  border-radius: 9999px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  text-decoration: none;
  transition: all 0.25s ease;
}

.compliance-btn:hover {
  background: rgba(99, 102, 241, 0.25);
  border-color: #818CF8;
  color: #FFFFFF;
  transform: translateY(-2px);
}

/* Contacts Section */
.contacts-wrapper {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2.5rem;
}

.contacts-card {
  background: rgba(18, 20, 32, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 2.2rem;
}

.contacts-box-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 1.5rem;
}

.contact-row {
  display: flex;
  align-items: flex-start;
  gap: 1.2rem;
  margin-bottom: 1.5rem;
}

.contact-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.contact-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748B;
  margin-bottom: 0.2rem;
}

.contact-val {
  font-size: 1rem;
  font-weight: 600;
  color: #FFFFFF;
}

.contact-val a {
  color: #FFFFFF;
  text-decoration: none;
  transition: color 0.2s ease;
}

.contact-val a:hover {
  color: #818CF8;
}

.contact-sub {
  font-size: 0.8rem;
  color: #64748B;
  margin-top: 0.15rem;
}

.cta-box {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.cta-box-desc {
  color: #94A3B8;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.cta-benefits {
  list-style: none;
  padding: 0;
  margin: 0 0 2rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  color: #E2E8F0;
  font-size: 0.9rem;
}

.cta-benefits li {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cta-btns {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.cta-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.85rem 1rem;
  border-radius: 14px;
  font-size: 0.92rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.25s ease;
}

.cta-btn-primary {
  background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35);
}

.cta-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5);
}

.cta-btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.cta-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

/* Footer */
.landing-footer {
  padding: 80px 0 30px;
  background: #05060A;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 3rem;
  margin-bottom: 3.5rem;
}

.footer-about {
  color: #94A3B8;
  font-size: 0.92rem;
  line-height: 1.6;
  margin-top: 1rem;
  max-width: 380px;
}

.footer-domain-tag {
  margin-top: 1rem;
  font-size: 0.82rem;
  color: #64748B;
}

.footer-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 1.25rem;
}

.footer-links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.footer-links a {
  color: #94A3B8;
  font-size: 0.88rem;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-links a:hover {
  color: #FFFFFF;
}

.footer-bottom-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.82rem;
  color: #64748B;
}

.footer-legal-links {
  display: flex;
  gap: 1.5rem;
}

.footer-legal-links a {
  color: #94A3B8;
  text-decoration: none;
}

.footer-legal-links a:hover {
  color: #FFFFFF;
}

/* Responsive Breakpoints */
@media (max-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1fr;
    text-align: center;
    gap: 3rem;
  }
  .hero-desc {
    margin: 0 auto 2.2rem;
  }
  .hero-actions-row {
    justify-content: center;
  }
  .hero-stats-row {
    max-width: 500px;
    margin: 0 auto;
  }
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .integration-banner {
    grid-template-columns: 1fr;
  }
  .contacts-wrapper {
    grid-template-columns: 1fr;
  }
  .compliance-cards-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  /* Header & Mobile Hamburger */
  .landing-header {
    height: 64px;
  }
  .landing-container {
    padding: 0 1.25rem;
  }
  .brand-logo {
    gap: 0.5rem;
  }
  .brand-logo-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
    font-size: 1rem;
  }
  .brand-logo-text {
    font-size: 1.15rem;
    white-space: nowrap;
    letter-spacing: -0.01em;
  }
  .nav-menu {
    display: none;
  }
  /* On mobile, collapse action buttons into hamburger drawer */
  .nav-actions .nav-btn {
    display: none;
  }
  .mobile-toggle-btn {
    display: flex;
  }
  .mobile-dropdown {
    top: 64px;
    max-height: calc(100vh - 64px);
  }
  .mobile-backdrop {
    top: 64px;
  }

  /* Hero Section */
  .hero-section {
    padding: 92px 0 45px;
  }
  .hero-grid {
    gap: 2.5rem;
  }
  .hero-badge {
    font-size: 0.74rem;
    padding: 0.35rem 0.8rem;
    line-height: 1.35;
    white-space: normal;
    text-align: center;
  }
  .hero-title {
    font-size: 2rem;
    line-height: 1.2;
    margin-bottom: 1rem;
  }
  .hero-desc {
    font-size: 0.94rem;
    line-height: 1.6;
    margin-bottom: 1.6rem;
  }
  .hero-actions-row {
    flex-direction: column;
    width: 100%;
    gap: 0.75rem;
  }
  .hero-cta-btn {
    width: 100%;
    height: 48px;
    justify-content: center;
    font-size: 0.92rem;
  }
  .hero-stats-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
    margin-top: 1.75rem;
    padding-top: 1.25rem;
  }
  .stat-cell {
    padding: 0.5rem 0.25rem;
  }
  .stat-cell h3 {
    font-size: 1.35rem;
  }
  .stat-cell p {
    font-size: 0.72rem;
    line-height: 1.25;
  }

  /* Interactive Smartphone Showcase */
  .card-switcher {
    width: 100%;
    max-width: 350px;
    gap: 4px;
    padding: 4px;
    margin: 0 auto 1.5rem;
  }
  .card-switch-tab {
    padding: 7px 10px;
    font-size: 0.76rem;
  }
  .phone-chassis {
    width: 285px;
    height: 550px;
    border-radius: 42px;
    margin: 0 auto;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.75), 0 0 35px rgba(99, 102, 241, 0.2);
  }
  .phone-screen {
    border-radius: 36px;
  }

  /* Section Common Spacing */
  .features-section,
  .wallets-section,
  .integration-section,
  .compliance-section,
  .contacts-section {
    padding: 45px 0;
  }
  .section-header {
    margin-bottom: 2.25rem;
  }
  .section-title {
    font-size: 1.75rem;
    line-height: 1.25;
  }
  .section-desc {
    font-size: 0.92rem;
  }

  /* Single Column Grids */
  .features-grid,
  .wallet-cards-grid,
  .compliance-cards-row,
  .contacts-wrapper {
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }
  .feature-card,
  .wallet-card,
  .compliance-card,
  .contacts-info-card,
  .cta-box {
    padding: 1.5rem;
    border-radius: 18px;
  }

  /* Integration Banner */
  .integration-banner {
    grid-template-columns: 1fr;
    padding: 1.75rem 1.25rem;
    gap: 2rem;
    border-radius: 20px;
  }
  .integration-title {
    font-size: 1.6rem;
  }
  .tech-chips {
    gap: 0.4rem;
  }
  .tech-chip {
    font-size: 0.75rem;
    padding: 0.35rem 0.75rem;
  }

  /* Contacts CTA */
  .cta-btns {
    flex-direction: column;
    width: 100%;
    gap: 0.75rem;
  }
  .cta-btn {
    width: 100%;
    height: 48px;
    justify-content: center;
  }

  /* Footer */
  .landing-footer {
    padding: 40px 0 25px;
  }
  .footer-grid {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  .footer-bottom-bar {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  .footer-legal-links {
    flex-wrap: wrap;
    justify-content: center;
    gap: 1rem;
  }
}

@media (max-width: 480px) {
  .brand-logo-text {
    font-size: 1.05rem;
  }
  .hero-title {
    font-size: 1.75rem;
  }
  .hero-stats-row {
    gap: 0.25rem;
  }
  .stat-cell {
    padding: 0.5rem 0.15rem;
  }
  .stat-cell h3 {
    font-size: 1.2rem;
  }
  .stat-cell p {
    font-size: 0.68rem;
  }
  .card-switcher {
    max-width: 320px;
  }
  .card-switch-tab {
    padding: 6px 7px;
    font-size: 0.72rem;
  }
  .phone-chassis {
    width: 265px;
    height: 520px;
    border-radius: 38px;
  }
  .section-title {
    font-size: 1.55rem;
  }
  .cta-box {
    padding: 1.25rem;
  }
}
</style>
