<template>
  <div class="min-h-screen relative flex flex-col page-p overflow-hidden">
    <div class="absolute w-[220px] h-[220px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Header -->
    <div class="flex items-center gap-3 z-10 mb-6 mt-4">
      <button @click="$router.push('/')" class="w-10 h-10 rounded-full bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center justify-center text-[color:var(--text)] hover:opacity-80 transition-colors">
        <svg class="w-5 h-5 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6"/>
        </svg>
      </button>
      <div class="flex flex-col">
        <h1 class="text-xl font-extrabold text-[color:var(--text)] tracking-tight">Кабинет владельца</h1>
        <span class="text-xs text-[color:var(--muted)] font-bold">{{ auth.organization?.name }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center z-10">
      <span class="inline-block w-8 h-8 border-4 border-[color:var(--gold)]/30 border-t-[color:var(--gold)] rounded-full animate-spin"></span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex-1 flex flex-col items-center justify-center text-center z-10 gap-3">
      <div class="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center text-red-500 mb-2">
        <svg class="w-8 h-8 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <p class="text-[color:var(--text)] font-bold">{{ error }}</p>
      <button @click="fetchData" class="px-6 py-2 rounded-full border border-[color:var(--gold)] text-[color:var(--gold)] font-bold text-sm mt-2 active:scale-95 transition-transform">
        Повторить
      </button>
    </div>

    <!-- Content -->
    <div v-else class="flex flex-col gap-4 z-10 pb-6">
      <!-- Main Metric: Visits Today -->
      <div class="card-luxury p-5 flex flex-col relative overflow-hidden shadow-lg" style="margin: 0; background: linear-gradient(135deg, rgba(201, 168, 76, 0.15) 0%, rgba(201, 168, 76, 0.05) 100%); border-color: rgba(201, 168, 76, 0.3);">
        <div class="absolute top-0 right-0 w-32 h-32 rounded-full pointer-events-none opacity-20"
             style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%); transform: translate(30px, -30px);"></div>
        <span class="text-[10px] uppercase tracking-wider text-[color:var(--gold)] font-extrabold mb-1 z-10 opacity-80">
          Пользовались сегодня
        </span>
        <div class="flex items-baseline gap-2 z-10">
          <span class="text-4xl font-black text-[color:var(--text)] tracking-tight">
            {{ metrics.used_today }}
          </span>
          <span class="text-xs font-bold text-[color:var(--muted)]">клиентов</span>
        </div>
      </div>

      <!-- Grid Metrics: Key Totals -->
      <div class="grid grid-cols-2 gap-3.5 mt-1">
        <!-- New Registrations -->
        <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
          <div class="w-8 h-8 rounded-full bg-green-500/10 text-green-500 flex items-center justify-center mb-3">
            <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/>
              <line x1="22" y1="11" x2="16" y2="11"/>
            </svg>
          </div>
          <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
            Новые сегодня
          </span>
          <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
            +{{ metrics.new_registrations_today }}
          </span>
        </div>

        <!-- Total Users -->
        <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
          <div class="w-8 h-8 rounded-full bg-blue-500/10 text-blue-500 flex items-center justify-center mb-3">
            <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
          </div>
          <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
            Всего клиентов
          </span>
          <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
            {{ Number(metrics.total_users || 0).toLocaleString('ru-RU') }}
          </span>
        </div>

        <!-- Accumulated Points (Full width banner card) -->
        <div class="col-span-2 card-luxury p-4 flex items-center justify-between shadow-md" style="margin: 0;">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-full bg-[color:var(--gold)]/10 text-[color:var(--gold)] flex items-center justify-center shrink-0">
              <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </div>
            <div class="flex flex-col">
              <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold">
                Баллов на руках
              </span>
              <span class="text-[11px] text-[color:var(--muted)] font-medium">Суммарный баланс</span>
            </div>
          </div>
          <span class="text-xl font-black text-[color:var(--gold)] tracking-tight">
            {{ formatPoints(metrics.accumulated_points) }}
          </span>
        </div>
      </div>

      <!-- Channels & Wallets Section -->
      <div class="mt-2 flex flex-col gap-2.5">
        <div class="flex items-center justify-between px-1">
          <span class="text-[10px] uppercase tracking-wider text-[color:var(--gold)] font-extrabold opacity-90">
            Каналы и кошельки
          </span>
          <span class="text-[10px] text-[color:var(--muted)] font-semibold">
            от базы клиентов
          </span>
        </div>

        <div class="grid grid-cols-2 gap-3.5">
          <!-- Telegram Users -->
          <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
            <div class="w-8 h-8 rounded-full bg-cyan-500/10 text-cyan-500 flex items-center justify-center mb-3">
              <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </div>
            <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
              В Telegram
            </span>
            <div class="flex items-baseline gap-1.5">
              <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
                {{ Number(metrics.telegram_users || 0).toLocaleString('ru-RU') }}
              </span>
              <span class="text-[10px] font-bold text-[color:var(--muted)]">
                ({{ calcPercent(metrics.telegram_users) }}%)
              </span>
            </div>
          </div>

          <!-- Web Onboarding Users -->
          <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
            <div class="w-8 h-8 rounded-full bg-purple-500/10 text-purple-400 flex items-center justify-center mb-3">
              <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="2" y1="12" x2="22" y2="12"/>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              </svg>
            </div>
            <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
              Веб-онбординг
            </span>
            <div class="flex items-baseline gap-1.5">
              <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
                {{ Number(metrics.web_onboarding_users || 0).toLocaleString('ru-RU') }}
              </span>
              <span class="text-[10px] font-bold text-[color:var(--muted)]">
                ({{ calcPercent(metrics.web_onboarding_users) }}%)
              </span>
            </div>
          </div>

          <!-- Google Wallet Users -->
          <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
            <div class="w-8 h-8 rounded-full bg-sky-500/10 text-sky-400 flex items-center justify-center mb-3">
              <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/>
              </svg>
            </div>
            <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
              Google Wallet
            </span>
            <div class="flex items-baseline gap-1.5">
              <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
                {{ Number(metrics.google_wallet_users || 0).toLocaleString('ru-RU') }}
              </span>
              <span class="text-[10px] font-bold text-[color:var(--muted)]">
                ({{ calcPercent(metrics.google_wallet_users) }}%)
              </span>
            </div>
          </div>

          <!-- Apple Wallet Users -->
          <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
            <div class="w-8 h-8 rounded-full bg-zinc-700/20 text-zinc-100 flex items-center justify-center mb-3 border border-white/5">
              <svg class="w-4 h-4 fill-current" viewBox="0 0 170 170">
                <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.19-2.12-9.97-3.17-14.34-3.17-4.58 0-9.49 1.05-14.74 3.17-5.26 2.13-9.5 3.24-12.74 3.35-4.35.13-9.16-1.9-14.42-6.08-3.7-3.04-7.7-7.85-12-14.44-6-9.15-10.74-19.64-14.23-31.48-3.48-11.83-5.23-23.08-5.23-33.74 0-14.3 3.5-26.11 10.5-35.43 7-9.32 15.7-14.07 26.1-14.26 4.9.11 10.05 1.35 15.45 3.73 5.4 2.38 9.21 3.63 11.44 3.76 1.8-.13 5.75-1.4 11.85-3.81 6.1-2.4 11.3-3.53 15.6-3.39 12.3.82 22.3 5.38 30 13.68-10.8 6.54-16.1 15.7-15.9 27.48.2 9.17 3.7 16.92 10.5 23.25 6.8 6.33 15.1 9.94 24.9 10.83-2.3 6.94-5.2 14.15-8.7 21.62zM119.22 31.85c0-7.07 2.6-13.7 7.8-19.89 5.2-6.19 11.6-10.26 19.2-12.21.8 3.59 1.1 6.89.9 9.9-.4 6.7-3.1 13.1-8.1 19.2-5 6.1-11.1 10.1-18.3 12-0.5-3.2-1.5-6.2-1.5-9z"/>
              </svg>
            </div>
            <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
              Apple Wallet
            </span>
            <div class="flex items-baseline gap-1.5">
              <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
                {{ Number(metrics.apple_wallet_users || 0).toLocaleString('ru-RU') }}
              </span>
              <span class="text-[10px] font-bold text-[color:var(--muted)]">
                ({{ calcPercent(metrics.apple_wallet_users) }}%)
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const auth = useAuthStore()

const isLoading = ref(true)
const error = ref(null)
const metrics = ref({
  used_today: 0,
  accumulated_points: 0,
  total_users: 0,
  telegram_users: 0,
  new_registrations_today: 0,
  web_onboarding_users: 0,
  google_wallet_users: 0,
  apple_wallet_users: 0
})

function formatPoints(val) {
  const num = Number(val)
  if (isNaN(num)) return '0'
  return num.toLocaleString('ru-RU', { maximumFractionDigits: 0 })
}

function calcPercent(val) {
  if (!metrics.value.total_users || metrics.value.total_users === 0) return 0
  const num = Number(val) || 0
  return Math.round((num / metrics.value.total_users) * 100)
}

async function fetchData() {
  isLoading.value = true
  error.value = null
  try {
    const res = await api.get('/loyalty/owner/dashboard/')
    metrics.value = res.data
  } catch (err) {
    error.value = 'Не удалось загрузить данные. Пожалуйста, попробуйте позже.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchData()
  
  // Haptic feedback
  const tg = window.Telegram?.WebApp
  if (tg?.HapticFeedback) {
    tg.HapticFeedback.impactOccurred('light')
  }
})
</script>
