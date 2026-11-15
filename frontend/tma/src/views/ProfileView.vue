<template>
  <div class="min-h-screen relative overflow-hidden flex flex-col">
    <!-- Dynamic radial glows -->
    <div class="absolute w-[220px] h-[220px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Content Container -->
    <div class="flex-1 page-p space-y-4 z-10 relative flex flex-col justify-start overflow-y-auto">
      
      <!-- Top Card: Header Title -->
      <div class="card-luxury text-left shadow-sm" style="margin-bottom: 0;">
        <h1 class="text-xl font-extrabold text-[color:var(--text)]">
          {{ isOnboarding ? t('onboardingNameTitle') : t('profile') }}
        </h1>
      </div>

      <!-- Employee Profile Card -->
      <div v-if="auth.canUploadInvoices || auth.isEmployee" 
           class="card-luxury p-4 flex flex-col gap-3 shadow-sm"
           style="background: linear-gradient(135deg, rgba(201, 168, 76, 0.16) 0%, rgba(201, 168, 76, 0.05) 100%); border-color: rgba(201, 168, 76, 0.35); margin-bottom: 0; margin-top: 12px;">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-11 h-11 rounded-2xl bg-white/10 flex items-center justify-center text-2xl border border-white/10 flex-shrink-0">
              {{ employeeRoleEmoji }}
            </div>
            <div class="flex flex-col text-left min-w-0">
              <span class="text-sm font-extrabold text-[color:var(--text)] leading-tight truncate">
                {{ auth.employee?.first_name || auth.customer?.first_name || 'Сотрудник' }} {{ auth.employee?.last_name || auth.customer?.last_name || '' }}
              </span>
              <span class="text-xs text-[color:var(--gold)] font-bold truncate">
                {{ employeeRoleLabel }} • {{ auth.organization?.name || '' }}
              </span>
            </div>
          </div>
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-green-500/15 text-green-400 border border-green-500/30 flex-shrink-0">
            Сотрудник
          </span>
        </div>

        <button @click="$router.push('/employee/invoices/create')" 
                class="btn-primary w-full py-2.5 text-xs flex items-center justify-center gap-2 mt-1">
          <svg class="w-4 h-4 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
            <circle cx="12" cy="13" r="4"/>
          </svg>
          <span>Загрузка накладной</span>
        </button>
      </div>
      
      <!-- Notification banner for onboarding -->
      <div v-if="isOnboarding" class="banner-warning p-4 flex items-start gap-3 animate-[scaleIn_0.2s_ease-out]" style="margin-top: 16px; margin-bottom: -8px;">
        <span class="text-xl flex-shrink-0">👋</span>
        <div class="text-xs banner-warning-text leading-relaxed text-left">
          <p class="banner-warning-title text-sm mb-0.5">{{ t('onboardingNameTitle') }}</p>
          <p>{{ t('onboardingNameDesc') }}</p>
        </div>
      </div>

      <!-- Notification banner if redirected from Google Wallet / home banner -->
      <div v-else-if="isRedirectedFromWallet" class="banner-warning p-4 flex items-start gap-3 animate-[scaleIn_0.2s_ease-out]" style="margin-top: 16px; margin-bottom: -8px;">
        <span class="text-xl flex-shrink-0">⚠️</span>
        <div class="text-xs banner-warning-text leading-relaxed text-left">
          <p class="banner-warning-title text-sm mb-0.5">{{ t('invalidNameTitle') }}</p>
          <p>{{ t('invalidNameDesc') }}</p>
        </div>
      </div>

      <!-- Profile Card Form -->
      <div class="card-luxury text-left flex flex-col shadow-sm gap-4" :style="{ marginBottom: 0, marginTop: '24px' }">
        
        <!-- First Name -->
        <div class="flex flex-col min-w-0 w-full">
          <label class="sheet-label">{{ t('firstName') }}</label>
          <input
            v-model="form.first_name"
            type="text"
            class="sheet-input"
            :placeholder="t('firstName')"
            required
          />
        </div>

        <!-- Last Name -->
        <div class="flex flex-col min-w-0 w-full">
          <label class="sheet-label">{{ t('lastName') }}</label>
          <input
            v-model="form.last_name"
            type="text"
            class="sheet-input"
            :placeholder="t('lastName')"
          />
        </div>

        <!-- Birthday -->
        <div class="flex flex-col min-w-0 w-full">
          <label class="sheet-label">{{ t('birthday') }}</label>
          <div class="relative w-full min-w-0">
            <input
              v-model="form.birthday"
              type="date"
              class="sheet-input"
              :max="maxDate"
            />
          </div>
        </div>

        <!-- Phone (Read Only) -->
        <div class="flex flex-col min-w-0 w-full opacity-60">
          <label class="sheet-label">{{ t('phoneLabel') }}</label>
          <input
            :value="auth.customer?.phone || ''"
            type="text"
            class="sheet-input cursor-not-allowed bg-[color:var(--bg-secondary)]"
            disabled
          />
        </div>

      </div>

      <!-- Action Button -->
      <div style="margin-top: 24px;">
        <button
          @click="saveProfile"
          :disabled="saving"
          class="btn-primary w-full"
        >
          <span v-if="saving" class="inline-block w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          <template v-else>
            {{ isOnboarding ? t('continue') : t('save') }}
          </template>
        </button>
      </div>

      <!-- Toast Alerts -->
      <Transition name="fade">
        <div v-if="toast.message" 
             class="fixed bottom-20 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-xl border text-xs font-semibold shadow-md z-50 text-center animate-[scaleIn_0.2s_ease-out]"
             :class="toast.isError ? 'bg-red-500/10 border-red-500/20 text-[color:var(--text-error)]' : 'bg-green-500/10 border-green-500/20 text-green-500'">
          {{ toast.message }}
        </div>
      </Transition>

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { t } from '@/i18n'
import { isValidName } from '@/services/validation'
import { safeStorage } from '@/services/storage'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const isOnboarding = computed(() => route.query.onboarding === '1')
const isRedirectedFromWallet = computed(() => route.query.reason === 'invalid_name')

const employeeRoleEmoji = computed(() => {
  const r = auth.employee?.role || auth.role
  const map = {
    chef: '👨‍🍳',
    barman: '🍹',
    purchaser: '📦',
    accountant: '💼',
    manager: '👔',
    owner: '👑',
    cashier: '💳',
  }
  return map[r] || '🧑‍🍳'
})

const employeeRoleLabel = computed(() => {
  if (auth.employee?.role_display) return auth.employee.role_display
  const r = auth.employee?.role || auth.role
  const map = {
    chef: 'Шеф-повар',
    barman: 'Бар-менеджер',
    purchaser: 'Закупщик',
    accountant: 'Бухгалтер',
    manager: 'Менеджер',
    owner: 'Владелец',
    cashier: 'Кассир',
  }
  return map[r] || 'Сотрудник'
})

const form = reactive({
  first_name: '',
  last_name: '',
  birthday: ''
})

const saving = ref(false)
const maxDate = ref(new Date().toISOString().split('T')[0])

const toast = reactive({
  message: '',
  isError: false
})

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

function showToast(msg, isErr = false) {
  toast.message = msg
  toast.isError = isErr
  setTimeout(() => {
    toast.message = ''
  }, 3000)
}

async function fetchProfileData() {
  try {
    const res = await api.get('/loyalty/customer/me/')
    auth.updateCustomer(res.data)
    initForm(res.data)
  } catch (e) {
    console.error('Error fetching customer details:', e)
  }
}

function initForm(customerData) {
  const rawFirst = customerData?.first_name || ''
  const rawLast = customerData?.last_name || ''
  // If imported name contains invalid characters (like a dot or emoji), do not populate garbage into input
  form.first_name = isValidName(rawFirst, true) ? rawFirst : ''
  form.last_name = isValidName(rawLast, false) ? rawLast : ''
  form.birthday = customerData?.birthday || ''
}

async function saveProfile() {
  const isFirstValid = isValidName(form.first_name, true)
  if (!isFirstValid) {
    triggerHaptic('notification', 'error')
    showToast(t('nameContainsInvalidChars'), true)
    return
  }

  const isLastValid = isValidName(form.last_name, false)
  if (!isLastValid) {
    triggerHaptic('notification', 'error')
    showToast(t('lastNameContainsInvalidChars'), true)
    return
  }

  saving.value = true
  triggerHaptic('impact', 'medium')

  try {
    const payload = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      birthday: form.birthday || null
    }

    const res = await api.patch('/loyalty/customer/me/', payload)
    auth.updateCustomer(res.data)
    initForm(res.data)
    
    // Clear onboarding flag
    safeStorage.removeItem('tma_onboarding_in_progress')

    triggerHaptic('notification', 'success')
    showToast(t('profileUpdated'), false)

    if (isOnboarding.value || isRedirectedFromWallet.value) {
      setTimeout(() => {
        router.replace('/')
      }, 1000)
    }
  } catch (e) {
    triggerHaptic('notification', 'error')
    const errMsg = e.response?.data?.first_name?.[0] || e.response?.data?.last_name?.[0] || e.response?.data?.error || t('profileError')
    showToast(errMsg, true)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  if (isOnboarding.value) {
    showToast(t('onboardingNameDesc'), false)
    triggerHaptic('impact', 'medium')
  } else if (isRedirectedFromWallet.value) {
    showToast(t('invalidNameToast'), true)
    triggerHaptic('notification', 'warning')
  }

  if (auth.customer) {
    initForm(auth.customer)
  }
  if (!auth.isLoading && auth.isAuthenticated) {
    fetchProfileData()
  }
})

watch(() => auth.isLoading, (loading) => {
  if (!loading && auth.isAuthenticated) {
    if (auth.customer) {
      initForm(auth.customer)
    }
    fetchProfileData()
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes scaleIn {
  from {
    transform: translate(-50%, 10px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translate(-50%, 0) scale(1);
    opacity: 1;
  }
}
</style>
