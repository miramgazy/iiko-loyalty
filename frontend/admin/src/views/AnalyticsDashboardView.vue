<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-white">Аналитический дашборд</h1>
      <p class="text-slate-400 text-sm mt-1">Ключевые метрики ресторана, динамика цен и стоп-листы</p>
    </div>

    <!-- Date selector & Sync button -->
    <div class="mb-8 flex flex-wrap gap-4 items-center justify-between">
      <div class="flex gap-3 items-center">
        <label class="text-sm text-slate-400 font-semibold">Дата анализа:</label>
        <input type="date" v-model="selectedDate" @change="loadAllData"
          class="bg-slate-900 border border-slate-800 text-white rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
      </div>
      
      <button 
        @click="syncOlapData" 
        :disabled="syncing"
        class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800/50 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/10 active:scale-[0.98]">
        <svg v-if="syncing" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg v-else class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
        </svg>
        <span>{{ syncing ? 'Обновление...' : 'Обновить данные из iiko' }}</span>
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <div v-else class="space-y-8">
      <!-- KPI Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <!-- Revenue -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Выручка</p>
          <p class="text-2xl font-bold text-white mt-2">{{ formatCurrency(kpi.revenue?.value) }}</p>
          <div class="flex flex-col gap-1 mt-4 text-[11px]">
            <span :class="kpi.revenue?.last_week_diff_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.revenue?.last_week_diff_pct >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.revenue?.last_week_diff_pct).toFixed(1) }}% к пред. неделе
            </span>
            <span :class="kpi.revenue?.last_month_diff_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.revenue?.last_month_diff_pct >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.revenue?.last_month_diff_pct).toFixed(1) }}% к пред. месяцу
            </span>
          </div>
        </div>

        <!-- Profit -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Валовая прибыль</p>
          <p class="text-2xl font-bold text-white mt-2">{{ formatCurrency(kpi.profit?.value) }}</p>
          <div class="flex flex-col gap-1 mt-4 text-[11px]">
            <span :class="kpi.profit?.last_week_diff_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.profit?.last_week_diff_pct >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.profit?.last_week_diff_pct).toFixed(1) }}% к пред. неделе
            </span>
            <span :class="kpi.profit?.last_month_diff_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.profit?.last_month_diff_pct >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.profit?.last_month_diff_pct).toFixed(1) }}% к пред. месяцу
            </span>
          </div>
        </div>

        <!-- Average Check -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Средний чек</p>
          <p class="text-2xl font-bold text-white mt-2">{{ formatCurrency(kpi.avg_check?.value) }}</p>
          <div class="flex flex-col gap-1 mt-4 text-[11px]">
            <span :class="kpi.avg_check?.last_week_diff_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.avg_check?.last_week_diff_pct >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.avg_check?.last_week_diff_pct).toFixed(1) }}% к пред. неделе
            </span>
          </div>
        </div>

        <!-- Guests -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Гости</p>
          <p class="text-2xl font-bold text-white mt-2">{{ kpi.guests_count?.value || 0 }}</p>
          <div class="flex flex-col gap-1 mt-4 text-[11px]">
            <span :class="kpi.guests_count?.last_week_diff_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.guests_count?.last_week_diff_pct >= 0 ? '▲' : '▼' }} {{ Math.abs(kpi.guests_count?.last_week_diff_pct).toFixed(1) }}% к пред. неделе
            </span>
          </div>
        </div>

        <!-- Food Cost -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <p class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Фудкост (%)</p>
          <p class="text-2xl font-bold text-white mt-2">{{ kpi.foodcost_percent?.value?.toFixed(1) }}%</p>
          <div class="flex flex-col gap-1 mt-4 text-[11px]">
            <span :class="kpi.foodcost_percent?.last_week_diff <= 0 ? 'text-emerald-400' : 'text-rose-400'">
              {{ kpi.foodcost_percent?.last_week_diff <= 0 ? '▼' : '▲' }} {{ Math.abs(kpi.foodcost_percent?.last_week_diff).toFixed(1) }}% к пред. неделе
            </span>
          </div>
        </div>
      </div>

      <!-- Price Drift & Stop Lists Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Price Drift -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
          <div class="px-6 py-5 border-b border-slate-800">
            <h2 class="font-bold text-white text-lg">Анализ инфляции сырья (Price Drift)</h2>
            <p class="text-xs text-slate-400 mt-1">Топ-10 подорожавших товаров по приходным накладным</p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th class="px-6 py-3">Товар</th>
                  <th class="px-6 py-3">Старая цена</th>
                  <th class="px-6 py-3">Новая цена</th>
                  <th class="px-6 py-3">Изменение</th>
                  <th class="px-6 py-3">Ущерб (Cost Impact)</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800 text-sm text-slate-200">
                <tr v-for="item in priceDrift" :key="item.product_id" class="hover:bg-slate-800/30">
                  <td class="px-6 py-4 font-medium text-white">{{ item.product_name }}</td>
                  <td class="px-6 py-4">{{ formatCurrency(item.price_old) }}</td>
                  <td class="px-6 py-4">{{ formatCurrency(item.price_new) }}</td>
                  <td class="px-6 py-4">
                    <span class="inline-flex items-center text-xs font-semibold"
                      :class="item.diff_percent >= 0 ? 'text-rose-400' : 'text-emerald-400'">
                      {{ item.diff_percent >= 0 ? '+' : '' }}{{ item.diff_percent.toFixed(1) }}%
                    </span>
                  </td>
                  <td class="px-6 py-4 font-semibold" :class="item.cost_impact >= 0 ? 'text-rose-400' : 'text-emerald-400'">
                    {{ item.cost_impact >= 0 ? '+' : '' }}{{ formatCurrency(item.cost_impact) }}
                  </td>
                </tr>
                <tr v-if="!priceDrift.length">
                  <td colspan="5" class="px-6 py-12 text-center text-slate-500">Нет данных по закупкам</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Stop Lists & Lost Revenue -->
        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
          <div class="px-6 py-5 border-b border-slate-800">
            <h2 class="font-bold text-white text-lg">Антирейтинг стоп-листов</h2>
            <p class="text-xs text-slate-400 mt-1">Оценка упущенной выручки и упущенной маржи</p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th class="px-6 py-3">Блюдо</th>
                  <th class="px-6 py-3">Начало</th>
                  <th class="px-6 py-3">Длительность</th>
                  <th class="px-6 py-3">Упущенная выручка</th>
                  <th class="px-6 py-3">Упущенная маржа</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800 text-sm text-slate-200">
                <tr v-for="list in stopLists" :key="list.id" class="hover:bg-slate-800/30">
                  <td class="px-6 py-4 font-medium text-white">{{ list.product_name }}</td>
                  <td class="px-6 py-4">{{ formatDate(list.started_at) }}</td>
                  <td class="px-6 py-4">{{ formatDuration(list.duration_seconds) }}</td>
                  <td class="px-6 py-4 text-rose-400 font-semibold">{{ formatCurrency(list.lost_revenue) }}</td>
                  <td class="px-6 py-4 text-rose-500">{{ formatCurrency(list.lost_profit) }}</td>
                </tr>
                <tr v-if="!stopLists.length">
                  <td colspan="5" class="px-6 py-12 text-center text-slate-500">Нет записей по стоп-листам</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(true)
const syncing = ref(false)
const selectedDate = ref(new Date().toISOString().substring(0, 10))

const kpi = ref({})
const priceDrift = ref([])
const stopLists = ref([])

async function loadAllData() {
  loading.value = true
  try {
    const orgId = auth.currentOrgId
    
    // Fetch KPI
    const kpiRes = await api.get(`/analytics/organizations/${orgId}/kpi/`, {
      params: { date: selectedDate.value }
    })
    kpi.value = kpiRes.data
    
    // Fetch Price Drift
    const driftRes = await api.get(`/inventory/organizations/${orgId}/price-drift/`)
    priceDrift.value = driftRes.data
    
    // Fetch Stop lists
    const stopRes = await api.get(`/inventory/organizations/${orgId}/stop-lists/`)
    stopLists.value = stopRes.data
  } catch (e) {
    toast.error('Не удалось загрузить данные аналитики')
  } finally {
    loading.value = false
  }
}

async function syncOlapData() {
  syncing.value = true
  try {
    const orgId = auth.currentOrgId
    const res = await api.post(`/analytics/organizations/${orgId}/sync/`, { days: 7 })
    if (res.data.success) {
      toast.success(res.data.message || 'Данные успешно обновлены!')
      await loadAllData()
    } else {
      toast.error(res.data.message || 'Не удалось обновить данные')
    }
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Произошла ошибка при обращении к серверу iiko'
    toast.error(errorMsg)
  } finally {
    syncing.value = false
  }
}

function formatCurrency(val) {
  if (val === undefined || val === null) return '0 ₸'
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'KZT', maximumFractionDigits: 0 }).format(val)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
  })
}

function formatDuration(sec) {
  if (sec === undefined || sec === null) return 'в стопе'
  const hours = Math.floor(sec / 3600)
  const mins = Math.floor((sec % 3600) / 60)
  if (hours > 0) {
    return `${hours} ч ${mins} мин`
  }
  return `${mins} мин`
}

onMounted(loadAllData)
</script>
