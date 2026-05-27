<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 px-4">
    <div class="w-full max-w-md">
      <!-- Header -->
      <div class="text-center mb-8">
        <div class="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-indigo-600/30">
          <span class="text-white text-2xl font-bold">L</span>
        </div>
        <h1 class="text-2xl font-bold text-white">LoyaltyAdmin</h1>
        <p class="text-slate-400 text-sm mt-1">Войдите в систему управления</p>
      </div>

      <!-- Card -->
      <div class="bg-slate-900 rounded-2xl border border-slate-800 p-8 shadow-2xl">
        <!-- Tabs -->
        <div class="flex bg-slate-800 rounded-xl p-1 mb-6 gap-1">
          <button
            id="tab-email"
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200"
            :class="activeTab === tab.id
              ? 'bg-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:text-white'"
          >
            {{ tab.label }}
          </button>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <!-- Email/Username tab -->
          <template v-if="activeTab === 'email'">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">
                Email или имя пользователя
              </label>
              <input
                id="input-username"
                v-model="form.username"
                type="text"
                placeholder="admin@example.com"
                autocomplete="username"
                required
                class="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                       placeholder:text-slate-500 transition-all"
              />
            </div>
          </template>

          <!-- Phone tab -->
          <template v-else>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">
                Номер телефона
              </label>
              <input
                id="input-phone"
                v-model="form.phone"
                type="tel"
                placeholder="+7 (7XX) XXX-XX-XX"
                autocomplete="tel"
                required
                class="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                       placeholder:text-slate-500 transition-all"
              />
            </div>
          </template>

          <!-- Password -->
          <div>
            <label class="block text-xs font-medium text-slate-400 mb-1.5">Пароль</label>
            <div class="relative">
              <input
                id="input-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="current-password"
                required
                class="w-full bg-slate-800 border border-slate-700 text-white rounded-xl px-4 py-3 text-sm
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                       placeholder:text-slate-500 transition-all pr-12"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {{ showPassword ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <!-- Error message -->
          <Transition name="slide-down">
            <div v-if="errorMsg" class="bg-red-950/60 border border-red-800 rounded-xl px-4 py-3">
              <p class="text-red-300 text-sm">{{ errorMsg }}</p>
            </div>
          </Transition>

          <!-- Submit -->
          <button
            id="btn-login"
            type="submit"
            :disabled="loading"
            class="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed
                   text-white font-semibold py-3 rounded-xl transition-all duration-200 flex items-center justify-center gap-2
                   shadow-lg shadow-indigo-600/20 hover:shadow-indigo-600/40 mt-2"
          >
            <span v-if="loading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            {{ loading ? 'Входим...' : 'Войти' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'
import { normalizePhone } from '@/utils/phone'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const tabs = [
  { id: 'email', label: 'Email / Логин' },
  { id: 'phone', label: 'Телефон' },
]
const activeTab = ref('email')
const form = ref({ username: '', phone: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  loading.value = true
  try {
    const username = activeTab.value === 'phone'
      ? normalizePhone(form.value.phone)
      : form.value.username

    const data = await auth.login(username, form.value.password)
    const memberships = data.user?.memberships || []

    if (memberships.length > 1 && !auth.isSuperAdmin) {
      router.push('/select-org')
    } else if (auth.isSuperAdmin) {
      router.push('/superadmin')
    } else {
      router.push('/admin/customers')
    }
    toast.success('Добро пожаловать!')
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.non_field_errors?.[0]
    errorMsg.value = detail || 'Неверные данные для входа'
  } finally {
    loading.value = false
  }
}
</script>
