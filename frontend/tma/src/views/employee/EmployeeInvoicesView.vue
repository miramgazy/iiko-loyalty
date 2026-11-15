<template>
  <div class="min-h-screen relative flex flex-col page-p overflow-x-hidden">
    <!-- Ambient gold background glow -->
    <div class="absolute w-[240px] h-[240px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Section Header: Мои накладные -->
    <div class="card-luxury p-4 text-left shadow-sm mb-4 z-10" style="margin-bottom: 16px;">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-lg font-black text-[color:var(--text)] tracking-tight">Мои накладные</h1>
          <p class="text-xs text-[color:var(--muted)] font-medium mt-0.5">Накладные, загруженные вами</p>
        </div>

        <button 
          @click="fetchInvoices" 
          :disabled="isLoading"
          class="p-2 rounded-xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] text-[color:var(--gold)] flex items-center justify-center hover:opacity-85 active:scale-95 transition-all cursor-pointer flex-shrink-0"
          title="Обновить"
        >
          <svg class="w-4 h-4 stroke-current" :class="{ 'animate-spin': isLoading }" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10"/>
            <polyline points="1 20 1 14 7 14"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Invoices List -->
    <div v-if="isLoading && invoices.length === 0" class="flex-1 flex items-center justify-center py-12 z-10">
      <div class="text-center">
        <span class="inline-block w-8 h-8 border-3 border-[color:var(--gold)]/30 border-t-[color:var(--gold)] rounded-full animate-spin mb-3"></span>
        <p class="text-xs text-[color:var(--muted)]">Загрузка накладных...</p>
      </div>
    </div>

    <div v-else-if="invoices.length === 0" class="card-luxury p-8 flex flex-col items-center justify-center text-center z-10 mb-4">
      <div class="w-14 h-14 rounded-2xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center justify-center text-3xl mb-3 shadow-inner">
        🧾
      </div>
      <h4 class="text-sm font-extrabold text-[color:var(--text)] mb-1">Пока нет накладных</h4>
      <p class="text-xs text-[color:var(--muted)] max-w-xs mb-4">
        Вы еще не отправляли накладные. Перейдите во вкладку «Загрузить», чтобы сфотографировать первую приходную накладную.
      </p>
      <button 
        @click="goToCreateInvoice"
        class="btn-primary py-2.5 px-4 text-xs flex items-center justify-center gap-2"
      >
        <span>+ Загрузить накладную</span>
      </button>
    </div>

    <div v-else class="flex flex-col gap-3 z-10 mb-4">
      <div 
        v-for="inv in invoices" 
        :key="inv.id" 
        class="card-luxury p-4 flex flex-col gap-2 relative shadow-sm text-left hover:border-[color:var(--gold)]/40 transition-colors"
        style="margin-bottom: 0;"
      >
        <!-- Top row: Doc number & Status badge -->
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <span class="text-xs font-black text-[color:var(--text)] tracking-tight truncate font-mono">
              {{ inv.invoice_number ? `№ ${inv.invoice_number}` : inv.internal_number }}
            </span>
            <span v-if="inv.pages_count" class="text-[10px] px-1.5 py-0.5 rounded bg-[color:var(--bg-secondary)] text-[color:var(--muted)] font-semibold flex-shrink-0">
              {{ inv.pages_count }} стр.
            </span>
          </div>

          <span 
            class="text-[10px] font-bold px-2 py-0.5 rounded-full border flex-shrink-0"
            :class="statusBadgeClass(inv.status)"
          >
            {{ inv.status_display || statusLabel(inv.status) }}
          </span>
        </div>

        <!-- Middle row: Supplier & Date -->
        <div class="flex items-center justify-between text-xs pt-1 border-t border-[color:var(--border)]/50">
          <div class="flex flex-col min-w-0 pr-2">
            <span class="text-[11px] text-[color:var(--muted)] font-medium">Поставщик:</span>
            <span class="font-bold text-[color:var(--text)] truncate text-xs">
              {{ inv.supplier_name_raw || inv.iiko_supplier_name || 'Определяется AI...' }}
            </span>
          </div>
          <div class="flex flex-col text-right flex-shrink-0">
            <span class="text-[11px] text-[color:var(--muted)] font-medium">Дата:</span>
            <span class="text-xs text-[color:var(--text)] font-semibold">
              {{ formatDate(inv.created_at) }}
            </span>
          </div>
        </div>

        <!-- Bottom row: Store & Total Sum -->
        <div class="flex items-center justify-between text-xs pt-1">
          <div class="flex items-center gap-1.5 text-[11px] text-[color:var(--muted)] min-w-0">
            <span class="truncate">📍 {{ inv.iiko_store_name || 'Склад не указан' }}</span>
          </div>
          <div v-if="inv.total_amount" class="text-xs font-black text-[color:var(--gold)] flex-shrink-0">
            {{ formatPrice(inv.total_amount) }} ₸
          </div>
        </div>

        <!-- Processing status hint if pending/processing -->
        <div v-if="['pending', 'processing'].includes(inv.status)" class="mt-1 p-2 rounded-lg bg-[color:var(--gold)]/10 border border-[color:var(--gold)]/20 text-[10px] text-[color:var(--gold)] flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-[color:var(--gold)] animate-ping"></span>
          <span>AI распознает накладную. Бухгалтер проверит черновик в веб-панели.</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const auth = useAuthStore()

const invoices = ref([])
const isLoading = ref(true)

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

function goToCreateInvoice() {
  triggerHaptic('impact', 'medium')
  router.push('/employee/invoices/create')
}

async function fetchInvoices() {
  isLoading.value = true
  triggerHaptic('impact', 'light')
  try {
    const res = await api.get('/invoices/documents/', {
      params: {
        only_my: 'true',
        organization_id: auth.organization?.id,
      }
    })
    invoices.value = Array.isArray(res.data) ? res.data : (res.data?.results || [])
  } catch (e) {
    console.error('Error fetching invoices:', e)
  } finally {
    isLoading.value = false
  }
}

function statusBadgeClass(status) {
  switch (status) {
    case 'pending':
    case 'processing':
      return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    case 'matched':
    case 'ready':
      return 'bg-blue-500/10 text-blue-400 border-blue-500/20'
    case 'exported':
      return 'bg-green-500/10 text-green-400 border-green-500/20'
    case 'error':
      return 'bg-red-500/10 text-red-400 border-red-500/20'
    default:
      return 'bg-white/10 text-[color:var(--muted)] border-white/10'
  }
}

function statusLabel(status) {
  switch (status) {
    case 'pending': return 'В очереди'
    case 'processing': return 'Распознавание'
    case 'matched': return 'Сопоставлена'
    case 'ready': return 'Готова'
    case 'exported': return 'В iiko'
    case 'error': return 'Ошибка'
    default: return status || 'Черновик'
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatPrice(val) {
  if (!val) return '0'
  return Math.round(Number(val)).toLocaleString('ru-RU')
}

onMounted(() => {
  fetchInvoices()
})
</script>
