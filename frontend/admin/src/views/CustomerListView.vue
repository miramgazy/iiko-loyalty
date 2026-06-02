<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">База клиентов</h1>
        <p class="text-slate-400 text-sm mt-1">Участники программы лояльности</p>
      </div>
      <button id="btn-export-csv" @click="exportCSV"
        class="border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 px-4 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-2">
        📥 Экспорт CSV
      </button>
    </div>

    <!-- Search -->
    <div class="mb-5 relative max-w-sm">
      <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">🔍</span>
      <input
        id="input-customer-search"
        v-model="search"
        type="text"
        placeholder="Поиск по имени или телефону..."
        class="w-full bg-slate-900 border border-slate-800 text-white rounded-xl pl-10 pr-4 py-3 text-sm
               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
               placeholder:text-slate-500 transition-all"
        @input="debouncedSearch"
      />
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div v-for="stat in stats" :key="stat.label" class="bg-slate-900 rounded-xl border border-slate-800 px-5 py-4">
        <p class="text-xs text-slate-500 mb-1">{{ stat.label }}</p>
        <p class="text-2xl font-bold text-white">{{ stat.value }}</p>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>
      <div v-else>
        <table class="w-full">
          <thead>
            <tr class="border-b border-slate-800">
              <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Клиент</th>
              <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Телефон</th>
              <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Баллы / Кошельки</th>
              <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">iiko</th>
              <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Рассылка</th>
              <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Дата</th>
              <th class="text-center px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Действие</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            <tr v-for="c in customers" :key="c.id" class="hover:bg-slate-800/50 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                    <span class="text-slate-300 text-xs font-bold">{{ initials(c) }}</span>
                  </div>
                  <div>
                    <p class="font-medium text-white text-sm">{{ c.first_name }} {{ c.last_name }}</p>
                    <p class="text-slate-600 text-xs">TG: {{ c.telegram_id }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span v-if="c.phone" class="text-sm text-slate-300 font-mono">{{ c.phone }}</span>
                <span v-else class="text-xs text-amber-600 bg-amber-900/30 border border-amber-800 px-2 py-0.5 rounded-full">Не подтверждён</span>
              </td>
              <td class="px-6 py-4">
                <!-- Total balance -->
                <span class="text-sm font-semibold text-indigo-300">{{ c.loyalty_balance?.toLocaleString('ru-RU') || '0' }}</span>
                <span class="text-slate-600 text-xs ml-1">pts</span>
                <!-- Individual wallets (if multi-wallet) -->
                <div v-if="c.wallets && c.wallets.length > 1" class="flex flex-col gap-1 mt-2">
                  <div v-for="w in c.wallets" :key="w.wallet_id || w.id"
                       class="flex items-center justify-between gap-2 text-xs px-2 py-1 rounded-lg border"
                       :class="w.wallet_type === 1
                         ? 'bg-amber-900/20 border-amber-800/40 text-amber-300'
                         : 'bg-indigo-900/20 border-indigo-800/40 text-indigo-300'">
                    <span class="truncate max-w-[90px] font-medium" :title="w.name">{{ w.name || 'Кошелёк' }}</span>
                    <span class="font-bold whitespace-nowrap">{{ Number(w.balance).toLocaleString('ru-RU') }}</span>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full mb-1"
                  :class="c.iiko_customer_id
                    ? 'bg-emerald-900/50 text-emerald-400 border border-emerald-800'
                    : 'bg-slate-800 text-slate-500 border border-slate-700'">
                  {{ c.iiko_customer_id ? '✓ Синхр.' : '— Нет' }}
                </span>
                <div v-if="c.iiko_card_number" class="text-xs text-slate-400 mt-1 font-mono">
                  💳 {{ c.iiko_card_number }}
                </div>
                <div v-if="c.iiko_categories?.length" class="flex flex-wrap gap-1 mt-1">
                  <span v-for="(cat, idx) in c.iiko_categories" :key="idx" class="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded border border-slate-700">
                    {{ cat.name }}
                  </span>
                </div>
              </td>
              <td class="px-6 py-4">
                <span v-if="c.is_bot_subscribed === true" class="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-950/50 text-emerald-400 border border-emerald-800/60">
                  ✓ Подписан
                </span>
                <span v-else-if="c.is_bot_subscribed === false" class="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-rose-950/50 text-rose-400 border border-rose-900/60">
                  ✗ Отписан
                </span>
                <span v-else class="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-500 border border-slate-700">
                  — Не решено
                </span>
              </td>
              <td class="px-6 py-4 text-xs text-slate-400">{{ formatDate(c.created_at) }}</td>
              <td class="px-6 py-4 text-center">
                <button
                  :id="'btn-sync-' + c.id"
                  @click="syncCustomer(c)"
                  :disabled="syncingId === c.id || !c.phone"
                  :title="c.phone ? 'Обновить данные из iiko' : 'Нет номера телефона'"
                  class="inline-flex items-center justify-center w-9 h-9 rounded-lg transition-all duration-200"
                  :class="syncingId === c.id
                    ? 'bg-indigo-900/40 text-indigo-400 cursor-wait'
                    : c.phone
                      ? 'bg-slate-800 text-slate-400 hover:bg-indigo-900/40 hover:text-indigo-300 border border-slate-700 hover:border-indigo-700'
                      : 'bg-slate-800/50 text-slate-600 cursor-not-allowed border border-slate-700/50'"
                >
                  <svg
                    class="w-4 h-4 transition-transform duration-300"
                    :class="{ 'animate-spin': syncingId === c.id }"
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round"
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              </td>
            </tr>
            <tr v-if="!customers.length">
              <td colspan="7" class="px-6 py-12 text-center text-slate-500">
                {{ search ? 'Клиенты не найдены' : 'Нет клиентов' }}
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div v-if="totalCount > 0" class="flex items-center justify-between px-6 py-4 border-t border-slate-800">
          <!-- Page size selector -->
          <div class="flex items-center gap-3">
            <span class="text-xs text-slate-500">Показывать по:</span>
            <div class="flex gap-1">
              <button
                v-for="size in [20, 50]" :key="size"
                @click="changePageSize(size)"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200"
                :class="pageSize === size
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'"
              >
                {{ size }}
              </button>
            </div>
            <span class="text-xs text-slate-500 ml-2">
              Всего: <span class="text-slate-300 font-medium">{{ totalCount }}</span>
            </span>
          </div>

          <!-- Page navigation -->
          <div class="flex items-center gap-1">
            <button
              @click="goToPage(currentPage - 1)"
              :disabled="currentPage <= 1"
              class="px-2.5 py-1.5 text-xs rounded-lg transition-all duration-200"
              :class="currentPage <= 1
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700'"
            >
              ←
            </button>
            <template v-for="p in visiblePages" :key="p">
              <span v-if="p === '...'" class="px-2 text-xs text-slate-600">...</span>
              <button
                v-else
                @click="goToPage(p)"
                class="px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200"
                :class="p === currentPage
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700'"
              >
                {{ p }}
              </button>
            </template>
            <button
              @click="goToPage(currentPage + 1)"
              :disabled="currentPage >= totalPages"
              class="px-2.5 py-1.5 text-xs rounded-lg transition-all duration-200"
              :class="currentPage >= totalPages
                ? 'text-slate-600 cursor-not-allowed'
                : 'text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-700'"
            >
              →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const customers = ref([])
const loading = ref(true)
const search = ref('')
let searchTimer = null

// Pagination state
const currentPage = ref(1)
const pageSize = ref(20)
const totalCount = ref(0)

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages = []
  pages.push(1)
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) {
    pages.push(i)
  }
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

// Sync state
const syncingId = ref(null)

const stats = computed(() => [
  { label: 'Всего клиентов', value: totalCount.value },
  { label: 'С номером телефона', value: customers.value.filter(c => c.phone).length },
  { label: 'Синхр. с iiko', value: customers.value.filter(c => c.iiko_customer_id).length },
  { label: 'Подписаны на бота', value: customers.value.filter(c => c.is_bot_subscribed === true).length },
])

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadCustomers()
  }, 350)
}

async function loadCustomers() {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (search.value.trim()) params.search = search.value.trim()
    const res = await api.get(`/loyalty/organizations/${auth.currentOrgId}/customers/`, { params })
    customers.value = res.data.results
    totalCount.value = res.data.count
  } catch {
    toast.error('Не удалось загрузить клиентов')
  } finally {
    loading.value = false
  }
}

function changePageSize(size) {
  pageSize.value = size
  currentPage.value = 1
  loadCustomers()
}

function goToPage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadCustomers()
}

async function syncCustomer(customer) {
  if (syncingId.value || !customer.phone) return
  syncingId.value = customer.id
  try {
    const res = await api.post(`/loyalty/organizations/${auth.currentOrgId}/customers/${customer.id}/sync/`)
    // Update customer in-place in the list
    const idx = customers.value.findIndex(c => c.id === customer.id)
    if (idx !== -1) {
      customers.value[idx] = res.data
    }
    toast.success(`Данные ${customer.first_name || 'клиента'} обновлены из iiko`)
  } catch (err) {
    const msg = err.response?.data?.error || 'Ошибка синхронизации с iiko'
    toast.error(msg)
  } finally {
    syncingId.value = null
  }
}

function exportCSV() {
  if (!customers.value.length) return toast.info('Нет данных для экспорта')
  const headers = ['ID', 'Имя', 'Фамилия', 'Телефон', 'Telegram ID', 'Баллы', 'iiko ID', 'Номер карты iiko', 'Рассылка', 'Дата']
  const rows = customers.value.map(c => [
    c.id, c.first_name, c.last_name, c.phone || '', c.telegram_id,
    c.loyalty_balance, c.iiko_customer_id || '', c.iiko_card_number || '',
    c.is_bot_subscribed === true ? 'Подписан' : (c.is_bot_subscribed === false ? 'Отписан' : 'Не решено'),
    c.created_at,
  ])
  const csv = [headers, ...rows].map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `customers_${auth.currentOrgId}_${new Date().toISOString().slice(0,10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('CSV экспортирован')
}

function initials(c) {
  return ((c.first_name?.[0] || '') + (c.last_name?.[0] || '')).toUpperCase() || '?'
}

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(loadCustomers)
</script>
