<template>
  <div class="tma-container">
    <!-- Loading state -->
    <div v-if="auth.isLoading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="w-10 h-10 border-[3px] rounded-full animate-spin mx-auto mb-4"
          :style="{ borderColor: 'var(--gold-glow)', borderTopColor: 'var(--gold)' }"></div>
        <p class="text-sm opacity-60">{{ t('loading') }}</p>
      </div>
    </div>

    <!-- Auth error -->
    <div v-else-if="auth.authError" class="flex-1 flex items-center justify-center p-6">
      <div class="text-center max-w-xs">
        <div class="text-4xl mb-4">🔐</div>
        <p class="text-sm opacity-70 mb-6">{{ auth.authError }}</p>
        <p class="text-xs opacity-40">{{ t('openFromTelegram') }}</p>
      </div>
    </div>

    <!-- Main content with persistent top header and bottom nav -->
    <div v-else class="flex-1 flex flex-col min-h-screen relative">
      <!-- Persistent Top Header -->
      <header v-if="showBottomNav" class="header">
        <div class="header-top">
          <!-- Logo and Company Name text -->
          <div class="header-brand text-left min-w-0 flex-1">
            <div v-if="theme.logoUrl" class="header-logo">
              <img :src="theme.logoUrl" alt="Logo" />
            </div>
            <div v-else class="header-logo text-2xl font-extrabold text-[color:var(--gold)]">
              {{ orgName?.[0] || 'L' }}
            </div>
            <div class="flex flex-col min-w-0">
              <span class="header-greeting">
                {{ theme.greetingText || t('welcome') }}
              </span>
              <span class="text-[16px] font-extrabold text-[color:var(--text)] leading-tight truncate">
                {{ orgName }}
              </span>
            </div>
          </div>

          <!-- Language Switcher & Social Links below it -->
          <div class="flex flex-col items-end gap-3 flex-shrink-0">
            <!-- Premium slide capsule language switcher -->
            <div class="lang-switcher bg-[color:var(--bg-secondary)] border border-[color:var(--border)] rounded-full p-[3px] flex relative gap-0 w-[84px] h-[28px] justify-between items-center shadow-inner">
              <div class="lang-slider absolute top-[2px] h-[calc(100%-4px)] rounded-full transition-all duration-200"
                   :style="{
                     left: locale === 'ru' ? '2px' : 'calc(50% + 1px)',
                     width: '38px',
                     background: 'var(--gold-gradient)'
                   }"></div>
              <button @click="changeLang('ru')" 
                      class="lang-pill w-[38px] text-center text-[10px] font-bold cursor-pointer transition-all duration-200 z-10 relative border-none bg-transparent py-0.5"
                      :style="{ color: locale === 'ru' ? 'var(--gold-text)' : 'var(--muted)' }">RU</button>
              <button @click="changeLang('kz')" 
                      class="lang-pill w-[38px] text-center text-[10px] font-bold cursor-pointer transition-all duration-200 z-10 relative border-none bg-transparent py-0.5"
                      :style="{ color: locale === 'kz' ? 'var(--gold-text)' : 'var(--muted)' }">KZ</button>
            </div>

            <!-- Social buttons in a single row -->
            <div v-if="auth.organization?.instagram_link || auth.organization?.whatsapp_link" class="social-btns flex gap-2">
              <button v-if="auth.organization?.instagram_link" 
                      @click="openSocialLink(auth.organization.instagram_link)" 
                      class="icon-btn bg-[color:var(--bg-secondary)] border border-[color:var(--border)] hover:opacity-85 text-[color:var(--text)] shadow-sm active:scale-90 transition-all duration-200">
                <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204 0-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.051.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/>
                </svg>
              </button>
              <button v-if="auth.organization?.whatsapp_link" 
                      @click="openSocialLink(auth.organization.whatsapp_link)" 
                      class="icon-btn bg-[color:var(--bg-secondary)] border border-[color:var(--border)] hover:opacity-85 text-[color:var(--text)] shadow-sm active:scale-90 transition-all duration-200">
                <svg class="w-4.5 h-4.5 fill-current" viewBox="0 0 24 24">
                  <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946C.06 5.348 5.397.01 12.008.01c3.202.001 6.212 1.246 8.477 3.514 2.266 2.268 3.507 5.28 3.505 8.484-.004 6.657-5.34 11.997-11.953 11.997-2.005-.001-3.973-.502-5.717-1.454L0 24zm6.59-4.846c1.6.95 3.197 1.451 4.82 1.452 5.423 0 9.835-4.409 9.839-9.83.002-2.628-1.021-5.1-2.885-6.964C16.598 1.958 14.13 .934 11.5 1.016c-5.424 0-9.835 4.411-9.84 9.832-.001 1.777.464 3.51 1.347 5.034l-.999 3.65 3.739-.978zm11.567-5.282c-.313-.156-1.854-.915-2.131-1.016-.277-.1-.478-.15-.678.15-.2.3-.775.976-.95 1.176-.176.2-.351.224-.664.068-.313-.156-1.322-.487-2.52-1.555-.931-.83-1.56-1.855-1.742-2.164-.183-.309-.02-.477.136-.632.14-.139.313-.365.469-.547.156-.183.208-.313.313-.522.104-.209.052-.391-.026-.547-.078-.156-.678-1.634-.93-2.24-.244-.589-.493-.51-.678-.519-.176-.009-.377-.01-.578-.01-.2 0-.528.075-.804.375-.276.3-.1.975.1 1.975.2 1 .775 2.1 1.775 3 1.9 1.7 3.3 2.9 5.3 3.7.476.19 1 .3 1.5.3 1.1.2 2 .1 2.8-.1.8-.2 1.8-.7 2.1-1.4.3-.7.3-1.3.2-1.4-.1-.1-.3-.2-.6-.3z"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
      <!-- Persistent Bottom Navigation Bar -->
      <nav v-if="showBottomNav" class="bottom-nav">
        <div class="flex justify-around items-center h-full">
          <!-- Cards Tab -->
          <RouterLink to="/" class="flex flex-col items-center gap-0.5 text-[10px] font-bold transition-all duration-200"
                      :style="{ color: isRouteActive('/') ? 'var(--gold)' : 'var(--muted)' }">
            <svg class="w-6 h-6 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2">
              <rect x="2" y="5" width="20" height="14" rx="2" />
              <line x1="2" y1="10" x2="22" y2="10" />
            </svg>
            <span>{{ t('cards') }}</span>
          </RouterLink>

          <!-- Info Tab -->
          <RouterLink to="/info" class="flex flex-col items-center gap-0.5 text-[10px] font-bold transition-all duration-200"
                      :style="{ color: isRouteActive('/info') ? 'var(--gold)' : 'var(--muted)' }">
            <svg class="w-6 h-6 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
            <span>{{ t('info') }}</span>
          </RouterLink>

          <!-- Profile Tab -->
          <RouterLink to="/profile" class="flex flex-col items-center gap-0.5 text-[10px] font-bold transition-all duration-200"
                      :style="{ color: isRouteActive('/profile') ? 'var(--gold)' : 'var(--muted)' }">
            <svg class="w-6 h-6 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>{{ t('profile') }}</span>
          </RouterLink>

          <!-- Close button -->
          <button @click="closeApp" class="flex flex-col items-center gap-0.5 text-[10px] font-bold transition-all duration-200 border-none bg-transparent cursor-pointer"
                  :style="{ color: 'var(--muted)' }">
            <svg class="w-6 h-6 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            <span>{{ t('close') }}</span>
          </button>
        </div>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { initTelegramWebApp } from '@/services/telegram'
import api from '@/services/api'
import { safeStorage } from '@/services/storage'

import { t, setLocale, locale } from '@/i18n'

const auth = useAuthStore()
const theme = useThemeStore()
const router = useRouter()
const route = useRoute()

const orgName = computed(() => auth.organization?.name || auth.customer?.organization?.name || '')

function triggerHaptic(type = 'impact', subtype = 'light') {
  const tg = window.Telegram?.WebApp
  if (tg?.HapticFeedback) {
    if (type === 'impact') {
      tg.HapticFeedback.impactOccurred(subtype)
    } else if (type === 'notification') {
      tg.HapticFeedback.notificationOccurred(subtype)
    } else if (type === 'selection') {
      tg.HapticFeedback.selectionChanged()
    }
  }
}

async function changeLang(lang) {
  setLocale(lang)
  triggerHaptic('impact', 'light')
  try {
    await api.patch('/loyalty/customer/me/', { language: lang })
    auth.updateCustomer({ language: lang })
  } catch (e) {
    console.error('Error changing language:', e)
  }
}

function openSocialLink(url) {
  if (!url) return
  if (window.Telegram?.WebApp?.openLink) {
    window.Telegram.WebApp.openLink(url)
  } else {
    window.open(url, '_blank')
  }
}

const showBottomNav = computed(() => {
  return !auth.isLoading && 
         !auth.authError && 
         auth.isOnboarded && 
         !auth.needsConsent &&
         route.name !== 'onboarding-lang' && 
         route.name !== 'onboarding-phone' &&
         route.name !== 'onboarding-consent'
})

function isRouteActive(path) {
  return route.path === path
}

function closeApp() {
  const tg = window.Telegram?.WebApp
  if (tg) {
    tg.close()
  } else {
    window.close()
  }
}

onMounted(async () => {
  // Initialize Telegram SDK
  const tg = initTelegramWebApp()
  
  if (tg) {
    const applyScheme = () => {
      const scheme = tg.colorScheme || 'dark'
      document.documentElement.classList.remove('tg-theme-dark', 'tg-theme-light')
      document.documentElement.classList.add(`tg-theme-${scheme}`)
    }
    applyScheme()
    tg.onEvent('themeChanged', applyScheme)
  } else {
    const applyBrowserScheme = () => {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      document.documentElement.classList.remove('tg-theme-dark', 'tg-theme-light')
      document.documentElement.classList.add(isDark ? 'tg-theme-dark' : 'tg-theme-light')
    }
    applyBrowserScheme()
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyBrowserScheme)
  }

  // Authenticate with backend
  const success = await auth.authenticate()


  if (success) {
    // Apply branding from organization settings
    theme.applyBranding(auth.organization?.branding)

    // Sync app locale with backend customer language setting
    if (auth.customer?.language) {
      setLocale(auth.customer.language)
    }

    // Navigate based on onboarding status
    if (!auth.isOnboarded) {
      const langSelected = safeStorage.getItem('tma_lang_selected') === 'true'
      router.replace(langSelected ? '/onboarding/phone' : '/onboarding/lang')
    } else if (auth.needsConsent) {
      router.replace('/onboarding/consent')
    } else {
      const onboardingRoutes = ['onboarding-lang', 'onboarding-phone', 'onboarding-consent']
      if (route.name === 'home' || onboardingRoutes.includes(route.name) || !route.name) {
        router.replace('/')
      }
    }
  }
})
</script>
