<template>
  <div class="min-h-screen relative flex flex-col page-p overflow-hidden">
    <!-- Ambient gold background glow -->
    <div class="absolute w-[240px] h-[240px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Employee Dedicated Header -->
    <div class="flex items-center justify-between z-10 mb-5 mt-2">
      <div class="flex items-center gap-3 min-w-0">
        <div class="w-11 h-11 rounded-2xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center justify-center text-xl flex-shrink-0 shadow-sm">
          {{ employeeRoleIcon }}
        </div>
        <div class="flex flex-col min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-base font-extrabold text-[color:var(--text)] tracking-tight truncate">
              {{ employeeDisplayName }}
            </span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[color:var(--gold)]/15 text-[color:var(--gold)] border border-[color:var(--gold)]/30 flex-shrink-0">
              {{ employeeRoleLabel }}
            </span>
          </div>
          <span class="text-xs text-[color:var(--muted)] font-medium truncate">
            {{ orgName }}
          </span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- Switch to Guest loyalty card if enabled -->
        <button 
          @click="goToGuestCard" 
          title="Карта гостя"
          class="h-9 px-2.5 rounded-xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center gap-1.5 text-xs font-bold text-[color:var(--text)] active:scale-95 transition-transform"
        >
          <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke-width="2">
            <rect x="2" y="5" width="20" height="14" rx="2" />
            <line x1="2" y1="10" x2="22" y2="10" />
          </svg>
          <span class="hidden sm:inline">Карта</span>
        </button>

        <!-- Close TMA button -->
        <button 
          @click="closeApp" 
          class="w-9 h-9 rounded-xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center justify-center text-[color:var(--muted)] active:scale-95 transition-transform"
        >
          <svg class="w-4 h-4 stroke-current" viewBox="0 0 24 24" fill="none" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Main CTA Card -->
    <div class="card-luxury p-5 flex flex-col relative overflow-hidden shadow-lg mb-5 z-10" 
         style="margin: 0; background: linear-gradient(135deg, rgba(201, 168, 76, 0.16) 0%, rgba(201, 168, 76, 0.05) 100%); border-color: rgba(201, 168, 76, 0.35);">
      <div class="flex items-center justify-between mb-3">
        <span class="text-[11px] uppercase tracking-wider text-[color:var(--gold)] font-extrabold flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[color:var(--gold)] animate-pulse"></span>
          Приемка товара
        </span>
        <span class="text-xs font-semibold text-[color:var(--muted)]">
          {{ invoices.length }} накладных
        </span>
      </div>

      <h2 class="text-lg font-black text-[color:var(--text)] tracking-tight mb-1.5">
        Загрузка накладной
      </h2>
      <p class="text-xs text-[color:var(--muted)] leading-relaxed mb-4">
        Сфотографируйте все страницы печатной или рукописной накладной. AI сам распознает товары и передаст черновик в iiko.
      </p>

      <button 
        @click="goToCreateInvoice"
        class="w-full py-3.5 px-4 rounded-xl font-extrabold text-sm flex items-center justify-center gap-2 shadow-md active:scale-[0.98] transition-all cursor-pointer"
        style="background: var(--gold-gradient); color: var(--gold-text);"
      >
        <svg class="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
          <circle cx="12" cy="13" r="4"/>
        </svg>
        <span>Сфотографировать накладную</span>
      </button>
    </div>

    <!-- Section Header & Refresh -->
    <div class="flex items-center justify-between mb-3 z-10">
      <div class="flex items-center gap-2">
        <h3 class="text-sm font-extrabold text-[color:var(--text)] uppercase tracking-wider">
          История загрузок
        </h3>
        <span v-if="isLoading" class="inline-block w-3.5 h-3.5 border-2 border-[color:var(--gold)]/30 border-t-[color:var(--gold)] rounded-full animate-spin"></span>
      </div>

      <button 
        @click="fetchInvoices" 
        :disabled="isLoading"
        class="text-xs font-bold text-[color:var(--gold)] flex items-center gap-1 hover:opacity-80 active:scale-95 transition-all"
      >
        <svg class="w-3.5 h-3.5 stroke-current" :class="{ 'animate-spin': isLoading }" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="23 4 23 10 17 10"/>
          <polyline points="1 20 1 14 7 14"/>
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
        </svg>
        <span>Обновить</span>
      </button>
    </div>

    <!-- Invoices List -->
    <div v-if="isLoading && invoices.length === 0" class="flex-1 flex items-center justify-center py-12 z-10">
      <div class="text-center">
        <span class="inline-block w-8 h-8 border-3 border-[color:var(--gold)]/30 border-t-[color:var(--gold)] rounded-full animate-spin mb-3"></span>
        <p class="text-xs text-[color:var(--muted)]">Загрузка накладных...</p>
      </div>
    </div>

    <div v-else-if="invoices.length === 0" class="card-luxury p-8 flex flex-col items-center justify-center text-center z-10">
      <div class="w-16 h-16 rounded-3xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center justify-center text-3xl mb-3 shadow-inner">
        🧾
      </div>
      <h4 class="text-sm font-extrabold text-[color:var(--text)] mb-1">Пока нет накладных</h4>
      <p class="text-xs text-[color:var(--muted)] max-w-xs mb-4">
        Вы еще не отправляли накладные. Нажмите кнопку выше, чтобы сфотографировать первую приходную накладную.
      </p>
      <button 
        @click="goToCreateInvoice"
        class="px-4 py-2 rounded-xl text-xs font-bold border border-[color:var(--gold)] text-[color:var(--gold)] active:scale-95 transition-transform"
      >
        + Загрузить накладную
      </button>
    </div>

    <div v-else class="flex flex-col gap-3 z-10 pb-10">
      <div 
        v-for="inv in invoices" 
        :key="inv.id" 
        class="card-luxury p-4 flex flex-col gap-2 relative shadow-sm border border-[color:var(--border)] hover:border-[color:var(--gold)]/40 transition-colors"
      >
        <!-- Top row: Doc number & Status badge -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5 min-w-0">
            <span class="text-xs font-black text-[color:var(--text)] tracking-tight truncate">
              {{ inv.invoice_number ? `№ ${inv.invoice_number}` : inv.internal_number }}
            </span>
            <span v-if="inv.pages_count" class="text-[10px] px-1.5 py-0.5 rounded bg-[color:var(--bg-secondary)] text-[color:var(--muted)] font-semibold">
              {{ inv.pages_count }} стр.
            </span>
          </div>

          <!-- Status Pill -->
          <span 
            class="px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 flex-shrink-0"
            :class="getStatusClasses(inv.status)"
          >
            <span v-if="inv.status === 'processing' || inv.status === 'pending'" class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
            {{ inv.status_display || getStatusText(inv.status) }}
          </span>
        </div>

        <!-- Middle row: Supplier & Store -->
        <div class="flex items-center justify-between text-xs text-[color:var(--muted)] pt-1">
          <span class="font-bold text-[color:var(--text)] truncate max-w-[65%]">
            {{ inv.iiko_supplier_name || inv.raw_supplier_name || 'Поставщик распознается...' }}
          </span>
          <span v-if="inv.total_sum" class="font-extrabold text-[color:var(--gold)]">
            {{ formatPrice(inv.total_sum) }} ₸
          </span>
        </div>

        <!-- Bottom row: Warehouse & Date -->
        <div class="flex items-center justify-between text-[11px] text-[color:var(--muted)] pt-1 border-t border-[color:var(--border)]/50 mt-1">
          <span class="flex items-center gap-1 truncate max-w-[60%]">
            <svg class="w-3 h-3 stroke-current flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            <span class="truncate">{{ inv.iiko_store_name || 'Склад не указан' }}</span>
          </span>
          <span>
            {{ formatDate(inv.created_at) }}
          </span>
        </div>

        <!-- Error note if failed -->
        <div v-if="inv.status === 'failed' && inv.error_message" class="text-[10px] text-red-500 bg-red-500/10 p-2 rounded-lg mt-1 font-medium">
          {{ inv.error_message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const auth = useAuthStore()

const invoices = ref([])
const isLoading = ref(false)
const error = ref(null)

const orgName = computed(() => auth.organization?.name || 'Ресторан')
const employeeDisplayName = computed(() => {
  if (auth.employee?.first_name || auth.employee?.last_name) {
    return `${auth.employee.first_name || ''} ${auth.employee.last_name || ''}`.trim()
  }
  return auth.customer?.first_name || 'Сотрудник'
})

const employeeRole = computed(() => auth.employee?.role || auth.role || 'employee')

const employeeRoleLabel = computed(() => {
  const map = {
    chef: 'Шеф-повар',
    cook: 'Повар',
    barman: 'Бармен',
    purchaser: 'Закупщик',
    accountant: 'Бухгалтер',
    admin: 'Администратор',
    waiter: 'Официант',
    hostess: 'Хостес',
    owner: 'Управляющий',
  }
  return auth.employee?.role_display || map[employeeRole.value] || 'Сотрудник'
})

const employeeRoleIcon = computed(() => {
  const map = {
    chef: '👨‍🍳',
    cook: '🍳',
    barman: '🍹',
    purchaser: '📦',
    accountant: '💼',
    admin: '👔',
    owner: '👑',
  }
  return map[employeeRole.value] || '🧑‍🍳'
})

function triggerHaptic(type = 'impact', subtype = 'light') {
  const tg = window.Telegram?.WebApp
  if (tg?.HapticFeedback) {
    if (type === 'impact') {
      tg.HapticFeedback.impactOccurred(subtype)
    } else if (type === 'notification') {
      tg.HapticFeedback.notificationOccurred(subtype)
    }
  }
}

async function fetchInvoices() {
  isLoading.value = true
  error.value = null
  triggerHaptic('impact', 'light')
  try {
    const res = await api.get('/invoices/documents/')
    // Handle paginated or non-paginated response
    invoices.value = res.data.results ? res.data.results : res.data
  } catch (e) {
    console.error('Error fetching invoices:', e)
    error.value = 'Не удалось загрузить список накладных'
  } finally {
    isLoading.value = false
  }
}

function goToCreateInvoice() {
  triggerHaptic('impact', 'medium')
  router.push('/employee/invoices/create')
}

function goToGuestCard() {
  triggerHaptic('impact', 'light')
  router.push('/')
}

function closeApp() {
  const tg = window.Telegram?.WebApp
  if (tg) tg.close()
  else window.close()
}

function formatPrice(val) {
  if (val == null) return '0'
  return Number(val).toLocaleString('ru-RU', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function formatDate(dtStr) {
  if (!dtStr) return ''
  try {
    const d = new Date(dtStr)
    return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return dtStr
  }
}

function getStatusText(status) {
  const map = {
    pending: 'В очереди',
    processing: 'Распознается AI',
    recognized: 'Распознан',
    approved: 'Согласован',
    sent_to_iiko: 'В iiko (Черновик)',
    failed: 'Ошибка',
  }
  return map[status] || status
}

function getStatusClasses(status) {
  switch (status) {
    case 'sent_to_iiko':
      return 'bg-purple-500/15 text-purple-400 border border-purple-500/30'
    case 'approved':
    case 'recognized':
      return 'bg-green-500/15 text-green-400 border border-green-500/30'
    case 'processing':
    case 'pending':
      return 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
    case 'failed':
      return 'bg-red-500/15 text-red-400 border border-red-500/30'
    default:
      return 'bg-[color:var(--bg-secondary)] text-[color:var(--muted)]'
  }
}

onMounted(() => {
  fetchInvoices()
})
</script>

<style scoped>
.card-luxury {
  background: var(--card-bg);
  border-radius: var(--radius);
  border: 1px solid var(--border);
}
</style>
