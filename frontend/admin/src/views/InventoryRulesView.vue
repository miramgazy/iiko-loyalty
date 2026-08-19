<template>
  <div class="p-8">
    <div class="mb-8 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-white">Управление запасами и закупки</h1>
        <p class="text-slate-400 text-sm mt-1">Остатки по методу Min-Max, контроль порогов и отправка заказов</p>
      </div>
      
      <button v-if="activeTab === 'rules'" @click="openCreateRuleModal"
        class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition-all">
        + Создать правило
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex bg-slate-900 rounded-xl p-1 mb-6 gap-1 w-fit border border-slate-800">
      <button @click="activeTab = 'rules'"
        class="px-5 py-2 text-sm font-medium rounded-lg transition-all"
        :class="activeTab === 'rules' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'">
        Пороги Min-Max
      </button>
      <button @click="activeTab = 'orders'"
        class="px-5 py-2 text-sm font-medium rounded-lg transition-all"
        :class="activeTab === 'orders' ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'">
        Заказы поставщикам
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
    </div>

    <div v-else>
      <!-- TAB: Rules -->
      <div v-show="activeTab === 'rules'" class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
        <table class="w-full text-left">
          <thead>
            <tr class="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th class="px-6 py-4">Товар</th>
              <th class="px-6 py-4">Мин. остаток (Min)</th>
              <th class="px-6 py-4">Макс. остаток (Max)</th>
              <th class="px-6 py-4">Идеальная цена</th>
              <th class="px-6 py-4">Ответственный</th>
              <th class="px-6 py-4 text-right">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800 text-sm text-slate-200">
            <tr v-for="rule in rules" :key="rule.id" class="hover:bg-slate-800/30">
              <td class="px-6 py-4 font-semibold text-white">{{ rule.product_name }}</td>
              <td class="px-6 py-4">{{ rule.min_stock }}</td>
              <td class="px-6 py-4">{{ rule.max_stock }}</td>
              <td class="px-6 py-4">{{ formatCurrency(rule.target_price) }}</td>
              <td class="px-6 py-4">
                <span class="px-2 py-1 rounded bg-slate-800 text-slate-400 text-xs">
                  {{ getRoleDisplay(rule.responsible_role) }}
                </span>
              </td>
              <td class="px-6 py-4 text-right space-x-3">
                <button @click="openEditRuleModal(rule)" class="text-indigo-400 hover:text-indigo-300">Редактировать</button>
                <button @click="deleteRule(rule)" class="text-rose-400 hover:text-rose-300">Удалить</button>
              </td>
            </tr>
            <tr v-if="!rules.length">
              <td colspan="6" class="px-6 py-12 text-center text-slate-500">Правила не настроены. Создайте правило, чтобы включить алерты.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- TAB: Orders -->
      <div v-show="activeTab === 'orders'" class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
        <table class="w-full text-left">
          <thead>
            <tr class="border-b border-slate-800 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th class="px-6 py-4">Заказ</th>
              <th class="px-6 py-4">Поставщик</th>
              <th class="px-6 py-4">Позиций</th>
              <th class="px-6 py-4">Статус</th>
              <th class="px-6 py-4">Дата создания</th>
              <th class="px-6 py-4 text-right">Действие</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800 text-sm text-slate-200">
            <tr v-for="order in orders" :key="order.id" class="hover:bg-slate-800/30">
              <td class="px-6 py-4 font-semibold text-white">#{{ order.id }}</td>
              <td class="px-6 py-4">{{ order.supplier_name || 'Не выбран' }}</td>
              <td class="px-6 py-4">
                <span class="text-xs bg-slate-850 px-2 py-0.5 rounded text-indigo-400 cursor-pointer hover:underline" @click="viewOrderItems(order)">
                  {{ order.items?.length }} поз.
                </span>
              </td>
              <td class="px-6 py-4">
                <span class="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full"
                  :class="getStatusClass(order.status)">
                  {{ getStatusLabel(order.status) }}
                </span>
              </td>
              <td class="px-6 py-4 text-slate-400">{{ formatDate(order.created_at) }}</td>
              <td class="px-6 py-4 text-right">
                <button v-if="order.status === 'DRAFT'" @click="approveOrder(order)" :disabled="approving === order.id"
                  class="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs px-3 py-2 rounded-xl font-semibold transition-all">
                  {{ approving === order.id ? 'Отправка...' : 'Утвердить' }}
                </button>
                <span v-else class="text-xs text-slate-500 font-mono">{{ order.iiko_document_id ? 'iiko: ' + order.iiko_document_id.substring(0, 8) : '-' }}</span>
              </td>
            </tr>
            <tr v-if="!orders.length">
              <td colspan="6" class="px-6 py-12 text-center text-slate-500">Нет сформированных заказов.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Rule Modal -->
    <div v-if="showRuleModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-950 border border-slate-800 rounded-3xl p-8 w-full max-w-md shadow-2xl">
        <h2 class="text-lg font-bold text-white mb-6">{{ ruleModalMode === 'create' ? 'Создать правило' : 'Редактировать правило' }}</h2>
        <form @submit.prevent="saveRule" class="space-y-4">
          <div>
            <label class="form-label">Название ингредиента</label>
            <input v-model="ruleForm.product_name" type="text" class="form-input" placeholder="например: Картофель очищенный" required />
          </div>
          <div>
            <label class="form-label">UUID ингредиента (iiko)</label>
            <input v-model="ruleForm.product_id" type="text" class="form-input font-mono text-sm" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Минимум (Min)</label>
              <input v-model.number="ruleForm.min_stock" type="number" step="0.001" class="form-input" required />
            </div>
            <div>
              <label class="form-label">Максимум (Max)</label>
              <input v-model.number="ruleForm.max_stock" type="number" step="0.001" class="form-input" required />
            </div>
          </div>
          <div>
            <label class="form-label">Плановая цена закупа</label>
            <input v-model.number="ruleForm.target_price" type="number" class="form-input" required />
          </div>
          <div>
            <label class="form-label">Ответственная роль</label>
            <select v-model="ruleForm.responsible_role" class="form-input">
              <option value="chef">Шеф-повар / Кухня</option>
              <option value="barman">Бар-менеджер / Бар</option>
              <option value="purchaser">Закупщик</option>
              <option value="owner">Управляющий / Владелец</option>
            </select>
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" @click="showRuleModal = false" class="flex-1 border border-slate-850 text-slate-400 hover:text-white py-2.5 rounded-xl text-sm font-medium transition-all">Отмена</button>
            <button type="submit" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white py-2.5 rounded-xl text-sm font-semibold transition-all">Сохранить</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Items Modal -->
    <div v-if="showItemsModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-950 border border-slate-800 rounded-3xl p-8 w-full max-w-lg shadow-2xl">
        <h2 class="text-lg font-bold text-white mb-6">Позиции заказа #{{ selectedOrder.id }}</h2>
        <div class="max-h-60 overflow-y-auto space-y-3">
          <div v-for="item in selectedOrder.items" :key="item.id" class="flex justify-between border-b border-slate-850 pb-2 text-sm">
            <span class="text-slate-300 font-semibold">{{ item.product_name }}</span>
            <span class="text-white">{{ item.quantity }} ед.</span>
          </div>
        </div>
        <div class="flex justify-end pt-6">
          <button @click="showItemsModal = false" class="px-5 py-2 bg-slate-800 text-slate-200 rounded-xl hover:text-white transition-all text-sm font-medium">Закрыть</button>
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

const activeTab = ref('rules')
const loading = ref(true)
const rules = ref([])
const orders = ref([])
const approving = ref(null)

const showRuleModal = ref(false)
const ruleModalMode = ref('create')
const ruleForm = ref({
  id: null,
  product_name: '',
  product_id: '',
  min_stock: 0,
  max_stock: 0,
  target_price: 0,
  responsible_role: 'chef'
})

const showItemsModal = ref(false)
const selectedOrder = ref({})

async function loadData() {
  loading.value = true
  try {
    const orgId = auth.currentOrgId
    const rulesRes = await api.get(`/inventory/organizations/${orgId}/rules/`)
    rules.value = rulesRes.data
    
    const ordersRes = await api.get(`/inventory/organizations/${orgId}/orders/`)
    orders.value = ordersRes.data
  } catch (e) {
    toast.error('Не удалось загрузить данные')
  } finally {
    loading.value = false
  }
}

function openCreateRuleModal() {
  ruleModalMode.value = 'create'
  ruleForm.value = {
    id: null,
    product_name: '',
    product_id: '',
    min_stock: 0,
    max_stock: 0,
    target_price: 0,
    responsible_role: 'chef'
  }
  showRuleModal.value = true
}

function openEditRuleModal(rule) {
  ruleModalMode.value = 'edit'
  ruleForm.value = { ...rule }
  showRuleModal.value = true
}

async function saveRule() {
  const orgId = auth.currentOrgId
  try {
    if (ruleModalMode.value === 'create') {
      await api.post(`/inventory/organizations/${orgId}/rules/`, ruleForm.value)
      toast.success('Правило Min-Max создано')
    } else {
      await api.put(`/inventory/organizations/${orgId}/rules/${ruleForm.value.id}/`, ruleForm.value)
      toast.success('Правило Min-Max обновлено')
    }
    showRuleModal.value = false
    loadData()
  } catch {
    toast.error('Ошибка сохранения правила')
  }
}

async function deleteRule(rule) {
  if (!confirm(`Удалить правило для ${rule.product_name}?`)) return
  const orgId = auth.currentOrgId
  try {
    await api.delete(`/inventory/organizations/${orgId}/rules/${rule.id}/`)
    toast.success('Правило удалено')
    loadData()
  } catch {
    toast.error('Ошибка удаления правила')
  }
}

async function approveOrder(order) {
  approving.value = order.id
  const orgId = auth.currentOrgId
  try {
    await api.post(`/inventory/organizations/${orgId}/orders/${order.id}/approve/`)
    toast.success('Заказ успешно утвержден и отправлен в iiko!')
    loadData()
  } catch {
    toast.error('Не удалось утвердить заказ')
  } finally {
    approving.value = null
  }
}

function viewOrderItems(order) {
  selectedOrder.value = order
  showItemsModal.value = true
}

function getRoleDisplay(role) {
  const map = {
    chef: 'Шеф-повар',
    barman: 'Бармен',
    purchaser: 'Закупщик',
    owner: 'Владелец'
  }
  return map[role] || role
}

function getStatusLabel(status) {
  const map = {
    DRAFT: 'Черновик',
    APPROVED: 'Утвержден',
    SENT: 'Отправлен',
    FAILED: 'Ошибка'
  }
  return map[status] || status
}

function getStatusClass(status) {
  const map = {
    DRAFT: 'bg-slate-800 text-slate-400 border border-slate-700',
    APPROVED: 'bg-amber-950/50 text-amber-300 border border-amber-800',
    SENT: 'bg-emerald-950/50 text-emerald-300 border border-emerald-800',
    FAILED: 'bg-red-950/50 text-red-300 border border-red-800'
  }
  return map[status] || ''
}

function formatCurrency(val) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'KZT', maximumFractionDigits: 0 }).format(val)
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadData)
</script>

<style scoped>
.form-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: #94a3b8;
  margin-bottom: 0.375rem;
}
.form-input {
  width: 100%;
  background-color: #1e293b;
  border: 1px solid #334155;
  color: white;
  border-radius: 0.75rem;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  outline: none;
}
.form-input:focus {
  box-shadow: 0 0 0 2px rgba(99,102,241,0.5);
  border-color: transparent;
}
</style>
