<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white">Персонал TMA</h1>
        <p class="text-slate-400 text-sm mt-1">Управление сотрудниками Telegram Mini App (Владельцы, Менеджеры, Кассиры)</p>
      </div>
      <button id="btn-add-tma-employee" @click="showModal = true"
        class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold
               transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2">
        <span>+</span> Добавить сотрудника
      </button>
    </div>

    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-slate-800">
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Сотрудник</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Telegram ID</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Роль</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Статус</th>
            <th class="px-6 py-4"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="emp in employees" :key="emp.id" class="hover:bg-slate-800/50 transition-colors">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-indigo-600/20 border border-indigo-600/30 flex items-center justify-center flex-shrink-0">
                  <span class="text-indigo-300 text-sm font-bold">{{ initials(emp) }}</span>
                </div>
                <div>
                  <p class="font-medium text-white text-sm">{{ emp.first_name }} {{ emp.last_name || '' }}</p>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-slate-300 font-mono">{{ emp.telegram_id || '—' }}</td>
            <td class="px-6 py-4">
              <span class="text-xs font-medium px-2.5 py-1 rounded-full border"
                :class="roleClass(emp.role)">
                {{ roleLabel(emp.role) }}
              </span>
            </td>
            <td class="px-6 py-4">
              <button
                @click="toggleStatus(emp)"
                :disabled="toggling === emp.id"
                class="text-xs font-medium px-2.5 py-1 rounded-full border transition-all disabled:opacity-50"
                :class="emp.is_active
                  ? 'bg-emerald-950/50 text-emerald-400 border-emerald-800 hover:bg-emerald-900/30'
                  : 'bg-red-950/50 text-red-400 border-red-800 hover:bg-red-900/30'">
                {{ emp.is_active ? 'Активен' : 'Неактивен' }}
              </button>
            </td>
            <td class="px-6 py-4 text-right">
              <button
                @click="removeEmployee(emp)"
                :disabled="removing === emp.id"
                class="text-xs text-red-400 hover:text-red-300 px-3 py-1.5 rounded-lg border border-red-900/50
                       hover:bg-red-900/30 transition-all disabled:opacity-50"
              >
                Отозвать доступ
              </button>
            </td>
          </tr>
          <tr v-if="!employees.length">
            <td colspan="5" class="px-6 py-12 text-center text-slate-500">Нет сотрудников TMA</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add employee modal -->
    <Transition name="fade">
      <div v-if="showModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 rounded-2xl border border-slate-700 p-8 w-full max-w-md shadow-2xl">
          <h2 class="text-lg font-bold text-white mb-6">Добавить сотрудника TMA</h2>
          <form @submit.prevent="addEmployee" class="space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">Имя</label>
                <input id="input-emp-firstname" v-model="newEmp.first_name" type="text" class="form-input" placeholder="Иван" required />
              </div>
              <div>
                <label class="form-label">Фамилия</label>
                <input id="input-emp-lastname" v-model="newEmp.last_name" type="text" class="form-input" placeholder="Иванов" />
              </div>
            </div>
            <div>
              <label class="form-label">Telegram ID</label>
              <input id="input-emp-tg-id" v-model.number="newEmp.telegram_id" type="number" class="form-input" placeholder="123456789" required />
            </div>
            <div>
              <label class="form-label">Роль в TMA</label>
              <select id="select-emp-role" v-model="newEmp.role" class="form-input">
                <option value="owner">Владелец</option>
                <option value="manager">Менеджер</option>
                <option value="cashier">Кассир</option>
              </select>
            </div>

            <div class="flex gap-3 pt-2">
              <button type="button" @click="closeModal"
                class="flex-1 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 py-2.5 rounded-xl text-sm font-medium transition-all">
                Отмена
              </button>
              <button type="submit" :disabled="adding"
                class="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2">
                <span v-if="adding" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                {{ adding ? 'Добавляем...' : 'Добавить' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const employees = ref([])
const loading = ref(true)
const removing = ref(null)
const toggling = ref(null)
const showModal = ref(false)
const adding = ref(false)
const newEmp = ref({ first_name: '', last_name: '', telegram_id: null, role: 'owner' })

async function loadEmployees() {
  loading.value = true
  try {
    const res = await api.get(`/core/organizations/${auth.currentOrgId}/tma-employees/`)
    employees.value = res.data
  } catch {
    toast.error('Не удалось загрузить сотрудников TMA')
  } finally {
    loading.value = false
  }
}

async function addEmployee() {
  adding.value = true
  try {
    const payload = {
      first_name: newEmp.value.first_name,
      last_name: newEmp.value.last_name,
      telegram_id: newEmp.value.telegram_id,
      role: newEmp.value.role,
      is_active: true
    }
    const res = await api.post(`/core/organizations/${auth.currentOrgId}/tma-employees/`, payload)
    if (!employees.value.find(e => e.id === res.data.id)) {
      employees.value.unshift(res.data)
    }
    toast.success('Сотрудник TMA успешно добавлен')
    closeModal()
  } catch (e) {
    const msg = Object.values(e.response?.data || {}).flat().join(', ') || 'Ошибка добавления'
    toast.error(msg)
  } finally {
    adding.value = false
  }
}

async function removeEmployee(emp) {
  if (!confirm(`Отозвать доступ у сотрудника ${emp.first_name} ${emp.last_name || ''}?`)) return
  removing.value = emp.id
  try {
    await api.delete(`/core/organizations/${auth.currentOrgId}/tma-employees/${emp.id}/`)
    employees.value = employees.value.filter(e => e.id !== emp.id)
    toast.success('Сотрудник TMA удален')
  } catch {
    toast.error('Ошибка при удалении сотрудника')
  } finally {
    removing.value = null
  }
}

async function toggleStatus(emp) {
  toggling.value = emp.id
  try {
    const updatedStatus = !emp.is_active
    const res = await api.patch(`/core/organizations/${auth.currentOrgId}/tma-employees/${emp.id}/`, {
      is_active: updatedStatus
    })
    emp.is_active = res.data.is_active
    toast.success(`Статус изменен на: ${res.data.is_active ? 'Активен' : 'Неактивен'}`)
  } catch {
    toast.error('Не удалось изменить статус сотрудника')
  } finally {
    toggling.value = null
  }
}

function closeModal() {
  showModal.value = false
  newEmp.value = { first_name: '', last_name: '', telegram_id: null, role: 'owner' }
}

function initials(emp) {
  return ((emp.first_name?.[0] || '') + (emp.last_name?.[0] || '')).toUpperCase() || '?'
}

function roleLabel(role) {
  return { owner: 'Владелец', manager: 'Менеджер', cashier: 'Кассир' }[role] || role
}

function roleClass(role) {
  if (role === 'owner') {
    return 'bg-purple-900/50 text-purple-300 border-purple-800'
  } else if (role === 'manager') {
    return 'bg-indigo-900/50 text-indigo-300 border-indigo-800'
  } else {
    return 'bg-slate-800 text-slate-300 border-slate-700'
  }
}

onMounted(loadEmployees)
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
  transition: all 0.15s;
  outline: none;
}
.form-input:focus {
  box-shadow: 0 0 0 2px rgba(99,102,241,0.5);
  border-color: transparent;
}
.form-input::placeholder {
  color: #64748b;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
