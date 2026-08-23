<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-white">Аналитика по продажам</h1>
      <p class="text-slate-400 text-sm mt-1">Ключевые метрики ресторана, динамика цен, структура оплат и рейтинг официантов</p>
    </div>

    <!-- Tabs Header -->
    <div class="border-b border-slate-800 mb-8 flex flex-wrap gap-4 items-center justify-between">
      <div class="flex gap-2">
        <button 
          @click="changeTab('kpi')"
          :class="activeTab === 'kpi' ? 'border-b-2 border-indigo-500 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
          class="px-4 py-3 text-sm transition-all focus:outline-none">
          Основные показатели
        </button>
        <button 
          @click="changeTab('payments')"
          :class="activeTab === 'payments' ? 'border-b-2 border-indigo-500 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
          class="px-4 py-3 text-sm transition-all focus:outline-none">
          Структура оплат
        </button>
        <button 
          @click="changeTab('waiters')"
          :class="activeTab === 'waiters' ? 'border-b-2 border-indigo-500 text-white font-bold' : 'text-slate-400 hover:text-slate-200'"
          class="px-4 py-3 text-sm transition-all focus:outline-none">
          По официантам
        </button>
      </div>

      <!-- Actions Block -->
      <div class="flex flex-wrap gap-4 items-center mb-2">
        <!-- Date select -->
        <div class="flex gap-2 items-center bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300">
          <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Дата анализа:</label>
          <input type="date" v-model="selectedDate" @change="loadAllData"
            class="bg-transparent text-white focus:outline-none font-semibold" />
        </div>

        <!-- Sync Button for KPI tab -->
        <button 
          v-if="activeTab === 'kpi'"
          @click="syncKpiData" 
          :disabled="syncingKpi"
          class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800/50 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/10 active:scale-[0.98]">
          <svg v-if="syncingKpi" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
          </svg>
          <span>{{ syncingKpi ? 'Обновление показателей...' : 'Обновить показатели KPI' }}</span>
        </button>

        <!-- Sync Button for Payments tab -->
        <button 
          v-if="activeTab === 'payments'"
          @click="syncPaymentsData" 
          :disabled="syncingPayments"
          class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800/50 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/10 active:scale-[0.98]">
          <svg v-if="syncingPayments" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
          </svg>
          <span>{{ syncingPayments ? 'Обновление оплат...' : 'Обновить структуру оплат' }}</span>
        </button>

        <!-- Sync Button for Waiters tab -->
        <button 
          v-if="activeTab === 'waiters'"
          @click="syncWaitersData" 
          :disabled="syncingWaiters"
          class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800/50 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/10 active:scale-[0.98]">
          <svg v-if="syncingWaiters" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M9 11l3 3L22 4" />
          </svg>
          <span>{{ syncingWaiters ? 'Обновление официантов...' : 'Обновить официантов' }}</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <!-- Active Tab Contents -->
    <div v-else>
      <!-- KPI Tab Content -->
      <div v-if="activeTab === 'kpi'" class="space-y-8 animate-fadeIn">
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
          <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
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
          <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
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

      <!-- Payments Tab Content -->
      <div v-else-if="activeTab === 'payments'" class="space-y-6 animate-fadeIn">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg">
          <h2 class="font-bold text-white text-lg mb-1">Структура платежей</h2>
          <p class="text-xs text-slate-400 mb-6">Доля каждого платежного метода в общей дневной выручке</p>

          <div v-if="!payments.length" class="text-center py-16 text-slate-500">
            Нет данных по типам оплаты за эту дату. Нажмите кнопку обновления выше, чтобы загрузить данные из iiko.
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div v-for="pay in payments" :key="pay.payment_type" 
              class="bg-slate-800/20 border border-slate-800 rounded-2xl p-5 hover:border-indigo-500/40 transition-all flex flex-col justify-between">
              <div>
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">{{ pay.payment_type }}</span>
                <p class="text-2xl font-bold text-white mt-2">{{ formatCurrency(pay.revenue) }}</p>
              </div>
              <div class="mt-6">
                <div class="flex justify-between text-xs text-slate-400 mb-1">
                  <span>Доля от выручки</span>
                  <span class="font-semibold text-white">{{ calculatePaymentShare(pay.revenue) }}%</span>
                </div>
                <div class="w-full bg-slate-950 h-2 rounded-full overflow-hidden">
                  <div class="bg-indigo-500 h-full rounded-full transition-all duration-500" :style="{ width: calculatePaymentShare(pay.revenue) + '%' }"></div>
                </div>
                <div class="flex justify-between text-[11px] text-slate-500 mt-3">
                  <span>Количество чеков</span>
                  <span>{{ pay.checks_count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Waiters Tab Content -->
      <div v-else-if="activeTab === 'waiters'" class="space-y-6 animate-fadeIn">
        <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-lg">
          <div class="px-6 py-5 border-b border-slate-800 flex justify-between items-center">
            <div>
              <h2 class="font-bold text-white text-lg">Рейтинг официантов</h2>
              <p class="text-xs text-slate-400 mt-1">Показатели выручки, количества чеков, гостей и среднего чека официантов</p>
            </div>
          </div>
          
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  <th class="px-6 py-3 text-center w-20">Ранг</th>
                  <th class="px-6 py-3">Официант</th>
                  <th class="px-6 py-3">Выручка</th>
                  <th class="px-6 py-3">Доля</th>
                  <th class="px-6 py-3">Кол-во чеков</th>
                  <th class="px-6 py-3">Кол-во гостей</th>
                  <th class="px-6 py-3">Средний чек</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800 text-sm text-slate-200">
                <tr v-for="(waiter, index) in waiters" :key="waiter.waiter_name" class="hover:bg-slate-800/30 transition-colors">
                  <td class="px-6 py-4 text-center font-bold">
                    <span v-if="index === 0" class="text-xl">🥇</span>
                    <span v-else-if="index === 1" class="text-xl">🥈</span>
                    <span v-else-if="index === 2" class="text-xl">🥉</span>
                    <span v-else class="text-slate-500 text-xs">#{{ index + 1 }}</span>
                  </td>
                  <td class="px-6 py-4 font-semibold text-white">{{ waiter.waiter_name }}</td>
                  <td class="px-6 py-4 font-bold text-indigo-400">{{ formatCurrency(waiter.revenue) }}</td>
                  <td class="px-6 py-4">
                    <span class="text-xs font-semibold text-slate-400">{{ calculateWaiterShare(waiter.revenue) }}%</span>
                  </td>
                  <td class="px-6 py-4">{{ waiter.checks_count }}</td>
                  <td class="px-6 py-4">{{ waiter.guests_count }}</td>
                  <td class="px-6 py-4 font-medium text-emerald-400">{{ formatCurrency(waiter.avg_check) }}</td>
                </tr>
                <tr v-if="!waiters.length">
                  <td colspan="7" class="px-6 py-12 text-center text-slate-500">Нет данных по официантам за эту дату. Нажмите кнопку обновления выше, чтобы загрузить данные.</td>
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
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const loading = ref(true)
const activeTab = ref('kpi')

const syncingKpi = ref(false)
const syncingPayments = ref(false)
const syncingWaiters = ref(false)

const selectedDate = ref(new Date().toISOString().substring(0, 10))

const kpi = ref({})
const priceDrift = ref([])
const stopLists = ref([])
const payments = ref([])
const waiters = ref([])

function changeTab(tab) {
  activeTab.value = tab
  loadAllData()
}

const totalPaymentRevenue = computed(() => {
  return payments.value.reduce((sum, item) => sum + item.revenue, 0)
})

function calculatePaymentShare(revenue) {
  if (totalPaymentRevenue.value === 0) return 0
  return ((revenue / totalPaymentRevenue.value) * 100).toFixed(1)
}

const totalWaiterRevenue = computed(() => {
  return waiters.value.reduce((sum, item) => sum + item.revenue, 0)
})

function calculateWaiterShare(revenue) {
  if (totalWaiterRevenue.value === 0) return 0
  return ((revenue / totalWaiterRevenue.value) * 100).toFixed(1)
}

async function loadKpiData() {
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
}

async function loadPaymentsData() {
  const orgId = auth.currentOrgId
  const res = await api.get(`/analytics/organizations/${orgId}/payments/`, {
    params: { date: selectedDate.value }
  })
  payments.value = res.data
}

async function loadWaitersData() {
  const orgId = auth.currentOrgId
  const res = await api.get(`/analytics/organizations/${orgId}/waiters/`, {
    params: { date: selectedDate.value }
  })
  waiters.value = res.data
}

async function loadAllData() {
  loading.value = true
  try {
    if (activeTab.value === 'kpi') {
      await loadKpiData()
    } else if (activeTab.value === 'payments') {
      await loadPaymentsData()
    } else if (activeTab.value === 'waiters') {
      await loadWaitersData()
    }
  } catch (e) {
    toast.error('Не удалось загрузить данные аналитики')
  } finally {
    loading.value = false
  }
}

async function syncKpiData() {
  syncingKpi.value = true
  try {
    const orgId = auth.currentOrgId
    const res = await api.post(`/analytics/organizations/${orgId}/sync/`, { days: 7, report_type: 'kpi' })
    if (res.data.success) {
      toast.success(res.data.message || 'Показатели KPI успешно обновлены!')
      await loadKpiData()
    } else {
      toast.error(res.data.message || 'Не удалось обновить показатели')
    }
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Произошла ошибка при обращении к серверу iiko'
    toast.error(errorMsg)
  } finally {
    syncingKpi.value = false
  }
}

async function syncPaymentsData() {
  syncingPayments.value = true
  try {
    const orgId = auth.currentOrgId
    const res = await api.post(`/analytics/organizations/${orgId}/sync/`, { days: 7, report_type: 'payments' })
    if (res.data.success) {
      toast.success(res.data.message || 'Данные о типах оплаты успешно обновлены!')
      await loadPaymentsData()
    } else {
      toast.error(res.data.message || 'Не удалось обновить структуру оплат')
    }
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Произошла ошибка при обращении к серверу iiko'
    toast.error(errorMsg)
  } finally {
    syncingPayments.value = false
  }
}

async function syncWaitersData() {
  syncingWaiters.value = true
  try {
    const orgId = auth.currentOrgId
    const res = await api.post(`/analytics/organizations/${orgId}/sync/`, { days: 7, report_type: 'waiters' })
    if (res.data.success) {
      toast.success(res.data.message || 'Рейтинг официантов успешно обновлен!')
      await loadWaitersData()
    } else {
      toast.error(res.data.message || 'Не удалось обновить отчет по официантам')
    }
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Произошла ошибка при обращении к серверу iiko'
    toast.error(errorMsg)
  } finally {
    syncingWaiters.value = false
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

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.25s ease-out forwards;
}
</style>
