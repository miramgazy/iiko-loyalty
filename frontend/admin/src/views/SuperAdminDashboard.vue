<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white">Организации</h1>
        <p class="text-slate-400 text-sm mt-1">Управление ресторанными сетями в системе</p>
      </div>
      <button id="btn-new-org" @click="showModal = true"
        class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold
               transition-all shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/40 flex items-center gap-2">
        <span>+</span> Новая организация
      </button>
    </div>

    <!-- Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>
      <table v-else class="w-full">
        <thead>
          <tr class="border-b border-slate-800">
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Название</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Slug</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Статус</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Создан</th>
            <th class="px-6 py-4"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="org in orgs" :key="org.id" class="hover:bg-slate-800/50 transition-colors">
            <td class="px-6 py-4">
              <p class="font-medium text-white">{{ org.name }}</p>
            </td>
            <td class="px-6 py-4">
              <span class="text-sm text-slate-400 font-mono bg-slate-800 px-2 py-0.5 rounded-lg">{{ org.slug }}</span>
            </td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
                :class="org.is_active
                  ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-800'
                  : 'bg-red-900/50 text-red-300 border border-red-800'">
                <span class="w-1.5 h-1.5 rounded-full" :class="org.is_active ? 'bg-emerald-400' : 'bg-red-400'"></span>
                {{ org.is_active ? 'Активна' : 'Отключена' }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-slate-400">{{ formatDate(org.created_at) }}</td>
            <td class="px-6 py-4 text-right">
              <button
                @click="toggleActive(org)"
                :disabled="toggling === org.id"
                class="text-xs px-3 py-1.5 rounded-lg border transition-all disabled:opacity-50"
                :class="org.is_active
                  ? 'border-red-800 text-red-400 hover:bg-red-900/30'
                  : 'border-emerald-800 text-emerald-400 hover:bg-emerald-900/30'"
              >
                {{ org.is_active ? 'Отключить' : 'Активировать' }}
              </button>
            </td>
          </tr>
          <tr v-if="!orgs.length">
            <td colspan="5" class="px-6 py-12 text-center text-slate-500">Нет организаций</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <Transition name="fade">
      <div v-if="showModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 rounded-2xl border border-slate-700 p-8 w-full max-w-md shadow-2xl">
          <h2 class="text-lg font-bold text-white mb-6">Создать организацию</h2>
          <form @submit.prevent="createOrg" class="space-y-4">
            <div>
              <label class="form-label">Название ресторана</label>
              <input id="input-org-name" v-model="newOrg.name" type="text" class="form-input" placeholder="Бургер Кинг" required />
            </div>
            <div>
              <label class="form-label">Slug (уникальный ID)</label>
              <input id="input-org-slug" v-model="newOrg.slug" type="text" class="form-input" placeholder="burger-king" required
                pattern="[a-z0-9\-]+" title="Только строчные буквы, цифры и дефис" />
            </div>
            <div>
              <label class="form-label">Email владельца</label>
              <input id="input-org-owner-email" v-model="newOrg.owner_email" type="email" class="form-input" placeholder="owner@example.com" required />
            </div>

            <div v-if="createdPassword" class="bg-emerald-950/60 border border-emerald-800 rounded-xl p-4">
              <p class="text-xs text-emerald-400 font-medium mb-1">✅ Организация создана! Временный пароль:</p>
              <p class="font-mono text-emerald-300 text-sm bg-emerald-900/30 rounded-lg px-3 py-2 tracking-wider">{{ createdPassword }}</p>
              <p class="text-xs text-emerald-600 mt-1">Передайте пароль владельцу</p>
            </div>

            <div class="flex gap-3 pt-2">
              <button type="button" @click="closeModal"
                class="flex-1 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 py-2.5 rounded-xl text-sm font-medium transition-all">
                {{ createdPassword ? 'Закрыть' : 'Отмена' }}
              </button>
              <button v-if="!createdPassword" type="submit" :disabled="creating"
                class="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2">
                <span v-if="creating" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                {{ creating ? 'Создаём...' : 'Создать' }}
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
import { useToastStore } from '@/stores/toast'

const toast = useToastStore()
const orgs = ref([])
const loading = ref(true)
const toggling = ref(null)
const showModal = ref(false)
const creating = ref(false)
const createdPassword = ref('')
const newOrg = ref({ name: '', slug: '', owner_email: '' })

async function loadOrgs() {
  loading.value = true
  try {
    const res = await api.get('/core/organizations/')
    orgs.value = res.data
  } catch (e) {
    toast.error('Не удалось загрузить организации')
  } finally {
    loading.value = false
  }
}

async function toggleActive(org) {
  toggling.value = org.id
  try {
    await api.patch(`/core/organizations/${org.id}/`, { is_active: !org.is_active })
    org.is_active = !org.is_active
    toast.success(org.is_active ? 'Организация активирована' : 'Организация отключена')
  } catch {
    toast.error('Ошибка при изменении статуса')
  } finally {
    toggling.value = null
  }
}

async function createOrg() {
  creating.value = true
  try {
    const res = await api.post('/core/organizations/', newOrg.value)
    orgs.value.unshift(res.data)
    if (res.data.temp_password) {
      createdPassword.value = res.data.temp_password
    } else {
      toast.success('Организация создана')
      closeModal()
    }
  } catch (e) {
    const errors = e.response?.data
    const msg = typeof errors === 'object' ? Object.values(errors).flat().join(', ') : 'Ошибка создания'
    toast.error(msg)
  } finally {
    creating.value = false
  }
}

function closeModal() {
  showModal.value = false
  createdPassword.value = ''
  newOrg.value = { name: '', slug: '', owner_email: '' }
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short', year: 'numeric' })
}

onMounted(loadOrgs)
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
</style>

