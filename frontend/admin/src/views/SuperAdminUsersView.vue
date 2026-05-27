<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-white">Пользователи организаций</h1>
        <p class="text-slate-400 text-sm mt-1">Управление менеджерами ресторанных сетей</p>
      </div>
      <button id="btn-new-manager" @click="openCreateModal"
        class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-xl text-sm font-semibold
               transition-all shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/40 flex items-center gap-2">
        <span>+</span> Новый менеджер
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
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Менеджер</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Логин</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Организация</th>
            <th class="text-left px-6 py-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Контакты</th>
            <th class="px-6 py-4"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="user in managers" :key="user.id" class="hover:bg-slate-800/50 transition-colors">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-indigo-600/20 border border-indigo-600/30 flex items-center justify-center flex-shrink-0">
                  <span class="text-indigo-300 text-sm font-bold">{{ initials(user) }}</span>
                </div>
                <div>
                  <p class="font-medium text-white text-sm">
                    {{ user.first_name || 'Без' }} {{ user.last_name || 'имени' }}
                  </p>
                  <p class="text-xs" :class="user.is_active ? 'text-emerald-400' : 'text-red-400'">
                    {{ user.is_active ? 'Активен' : 'Заблокирован' }}
                  </p>
                </div>
              </div>
            </td>
            <td class="px-6 py-4">
              <span class="text-sm text-slate-300 font-mono bg-slate-800 px-2 py-0.5 rounded-lg">{{ user.username }}</span>
            </td>
            <td class="px-6 py-4 text-sm text-slate-400">
              {{ getOrganizationName(user) }}
            </td>
            <td class="px-6 py-4">
              <p class="text-sm text-slate-300">{{ user.email || '—' }}</p>
              <p class="text-xs text-slate-500">{{ user.phone || '—' }}</p>
            </td>
            <td class="px-6 py-4 text-right">
              <div class="flex gap-2 justify-end">
                <button
                  @click="openEditModal(user)"
                  class="text-xs text-indigo-400 hover:text-indigo-300 px-2.5 py-1.5 rounded-lg border border-slate-700 hover:border-indigo-500/50 transition-all"
                >
                  Изменить
                </button>
                <button
                  @click="deleteManager(user)"
                  :disabled="deleting === user.id"
                  class="text-xs text-red-400 hover:text-red-300 px-2.5 py-1.5 rounded-lg border border-red-950/50 hover:bg-red-950/30 transition-all disabled:opacity-50"
                >
                  Удалить
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!managers.length">
            <td colspan="5" class="px-6 py-12 text-center text-slate-500">Менеджеры не найдены</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <Transition name="fade">
      <div v-if="showModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 rounded-2xl border border-slate-700 p-8 w-full max-w-md shadow-2xl overflow-y-auto max-h-[90vh]">
          <h2 class="text-lg font-bold text-white mb-6">
            {{ isEditMode ? 'Редактировать менеджера' : 'Создать менеджера' }}
          </h2>
          <form @submit.prevent="submitForm" class="space-y-4">
            <!-- Organization Selector -->
            <div>
              <label class="form-label">Организация</label>
              <select id="select-manager-org" v-model="form.organization_id" class="form-input" required>
                <option value="" disabled>Выберите организацию</option>
                <option v-for="org in organizations" :key="org.id" :value="org.id">
                  {{ org.name }}
                </option>
              </select>
            </div>

            <!-- Login / Username -->
            <div>
              <label class="form-label">Логин (Имя пользователя)</label>
              <input id="input-manager-username" v-model="form.username" type="text" class="form-input" placeholder="ivan_manager" required />
            </div>

            <!-- Password -->
            <div>
              <label class="form-label">
                Пароль {{ isEditMode ? '(оставьте пустым для сохранения прежнего)' : '' }}
              </label>
              <input id="input-manager-password" v-model="form.password" type="password" class="form-input" placeholder="••••••••" :required="!isEditMode" />
            </div>

            <!-- Personal info -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="form-label">Имя</label>
                <input id="input-manager-firstname" v-model="form.first_name" type="text" class="form-input" placeholder="Иван" />
              </div>
              <div>
                <label class="form-label">Фамилия</label>
                <input id="input-manager-lastname" v-model="form.last_name" type="text" class="form-input" placeholder="Иванов" />
              </div>
            </div>

            <!-- Email -->
            <div>
              <label class="form-label">Email</label>
              <input id="input-manager-email" v-model="form.email" type="email" class="form-input" placeholder="manager@example.com" />
            </div>

            <!-- Phone -->
            <div>
              <label class="form-label">Телефон</label>
              <input id="input-manager-phone" v-model="form.phone" type="text" class="form-input" placeholder="+7 707 123 45 67" />
            </div>

            <!-- Is Active Toggle -->
            <div v-if="isEditMode" class="flex items-center gap-2 pt-2">
              <input id="checkbox-manager-active" type="checkbox" v-model="form.is_active" class="w-4 h-4 rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-500" />
              <label for="checkbox-manager-active" class="text-sm font-medium text-slate-300">Пользователь активен</label>
            </div>

            <!-- Form Actions -->
            <div class="flex gap-3 pt-4">
              <button type="button" @click="closeModal"
                class="flex-1 border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 py-2.5 rounded-xl text-sm font-medium transition-all">
                Отмена
              </button>
              <button type="submit" :disabled="saving"
                class="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2">
                <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                {{ saving ? 'Сохранение...' : (isEditMode ? 'Сохранить' : 'Создать') }}
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

const managers = ref([])
const organizations = ref([])
const loading = ref(true)
const saving = ref(false)
const deleting = ref(null)

const showModal = ref(false)
const isEditMode = ref(false)
const currentUserId = ref(null)

const form = ref({
  organization_id: '',
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  is_active: true
})

async function loadData() {
  loading.value = true
  try {
    const [usersRes, orgsRes] = await Promise.all([
      api.get('/accounts/superadmin/users/'),
      api.get('/core/organizations/')
    ])
    managers.value = usersRes.data
    organizations.value = orgsRes.data
  } catch (e) {
    toast.error('Не удалось загрузить данные')
  } finally {
    loading.value = false
  }
}

function getOrganizationName(user) {
  if (user.memberships && user.memberships.length > 0) {
    return user.memberships[0].organization.name
  }
  return '—'
}

function initials(user) {
  return ((user.first_name?.[0] || '') + (user.last_name?.[0] || '')).toUpperCase() || user.username?.[0]?.toUpperCase() || '?'
}

function openCreateModal() {
  isEditMode.value = false
  currentUserId.value = null
  form.value = {
    organization_id: '',
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    is_active: true
  }
  showModal.value = true
}

function openEditModal(user) {
  isEditMode.value = true
  currentUserId.value = user.id
  
  let orgId = ''
  if (user.memberships && user.memberships.length > 0) {
    orgId = user.memberships[0].organization.id
  }

  form.value = {
    organization_id: orgId,
    username: user.username,
    password: '',
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    phone: user.phone,
    is_active: user.is_active
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function submitForm() {
  saving.value = true
  try {
    const payload = { ...form.value }
    // Remove password if empty in edit mode
    if (isEditMode.value && !payload.password) {
      delete payload.password;
    }

    if (isEditMode.value) {
      const res = await api.put(`/accounts/superadmin/users/${currentUserId.value}/`, payload)
      const index = managers.value.findIndex(m => m.id === currentUserId.value)
      if (index !== -1) {
        managers.value[index] = res.data
      }
      toast.success('Менеджер успешно обновлен')
    } else {
      const res = await api.post('/accounts/superadmin/users/', payload)
      managers.value.unshift(res.data)
      toast.success('Менеджер успешно создан')
    }
    closeModal()
  } catch (e) {
    const errors = e.response?.data
    const msg = typeof errors === 'object' ? Object.values(errors).flat().join(', ') : 'Ошибка сохранения'
    toast.error(msg)
  } finally {
    saving.value = false
  }
}

async function deleteManager(user) {
  if (!confirm(`Удалить менеджера ${user.username}? Это действие безвозвратно удалит пользователя.`)) return
  deleting.value = user.id
  try {
    await api.delete(`/accounts/superadmin/users/${user.id}/`)
    managers.value = managers.value.filter(m => m.id !== user.id)
    toast.success('Менеджер удален')
  } catch (e) {
    toast.error('Не удалось удалить менеджера')
  } finally {
    deleting.value = null
  }
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
