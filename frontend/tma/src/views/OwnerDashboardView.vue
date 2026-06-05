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

      <!-- Grid Metrics -->
      <div class="grid grid-cols-2 gap-4 mt-2">
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
            {{ Number(metrics.total_users).toLocaleString('ru-RU') }}
          </span>
        </div>

        <!-- Accumulated Points -->
        <div class="card-luxury p-4 flex flex-col shadow-md" style="margin: 0;">
          <div class="w-8 h-8 rounded-full bg-[color:var(--gold)]/10 text-[color:var(--gold)] flex items-center justify-center mb-3">
            <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          </div>
          <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-extrabold mb-1">
            Баллов на руках
          </span>
          <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
            {{ formatPoints(metrics.accumulated_points) }}
          </span>
        </div>

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
          <div class="flex items-baseline gap-1">
            <span class="text-xl font-black text-[color:var(--text)] tracking-tight">
              {{ metrics.telegram_users }}
            </span>
            <span class="text-[10px] font-bold text-[color:var(--muted)]">
              ({{ metrics.total_users > 0 ? Math.round((metrics.telegram_users / metrics.total_users) * 100) : 0 }}%)
            </span>
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
  new_registrations_today: 0
})

function formatPoints(val) {
  const num = Number(val)
  if (isNaN(num)) return '0'
  return num.toLocaleString('ru-RU', { maximumFractionDigits: 0 })
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
