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
            </tr>
            <tr v-if="!customers.length">
              <td colspan="6" class="px-6 py-12 text-center text-slate-500">
                {{ search ? 'Клиенты не найдены' : 'Нет клиентов' }}
              </td>
            </tr>
          </tbody>
        </table>
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

const stats = computed(() => [
  { label: 'Всего клиентов', value: customers.value.length },
  { label: 'С номером телефона', value: customers.value.filter(c => c.phone).length },
  { label: 'Синхр. с iiko', value: customers.value.filter(c => c.iiko_customer_id).length },
  { label: 'Подписаны на бота', value: customers.value.filter(c => c.is_bot_subscribed === true).length },
])

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadCustomers, 350)
}

async function loadCustomers() {
  loading.value = true
  try {
    const params = {}
    if (search.value.trim()) params.search = search.value.trim()
    const res = await api.get(`/loyalty/organizations/${auth.currentOrgId}/customers/`, { params })
    customers.value = res.data
  } catch {
    toast.error('Не удалось загрузить клиентов')
  } finally {
    loading.value = false
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
