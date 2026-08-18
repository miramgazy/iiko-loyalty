<template>
  <div class="min-h-screen relative overflow-hidden flex flex-col">
    <!-- Background glows -->
    <div class="absolute w-[300px] h-[300px] rounded-full -top-[80px] left-1/2 -translate-x-1/2 pointer-events-none opacity-60"
         style="background: radial-gradient(circle, var(--gold-glow) 0%, transparent 70%);"></div>

    <!-- Main Content Container matching HomeView layout and padding -->
    <div class="flex-grow page-p z-10 relative flex flex-col justify-between"
         style="padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 24px); padding-top: calc(env(safe-area-inset-top, 0px) + 24px);">

      <!-- Top Section: Phone Animation Icon, Title, Subtitle -->
      <div class="flex flex-col items-center text-center w-full mt-6">
        <!-- Phone Animation Icon -->
        <div class="relative flex items-center justify-center w-24 h-24 mb-10">
          <div class="absolute border rounded-full pointer-events-none animate-wave-expand w-[110px] h-[110px]" style="border-color: var(--gold-glow); animation-delay: 0s;"></div>
          <div class="absolute border rounded-full pointer-events-none animate-wave-expand w-[140px] h-[140px]" style="border-color: var(--gold-glow); animation-delay: 0.6s;"></div>
          <div class="absolute border rounded-full pointer-events-none animate-wave-expand w-[170px] h-[170px]" style="border-color: var(--gold-glow); animation-delay: 1.2s;"></div>
          
          <div class="absolute w-[72px] h-[72px] rounded-[26px] flex items-center justify-center text-4xl border"
               :style="{ 
                 background: `linear-gradient(135deg, var(--gold-glow), rgba(255,255,255,0.02))`,
                 borderColor: 'var(--border)'
               }">
            <svg class="w-8 h-8 text-[color:var(--text)] opacity-90 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
              <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
          </div>
        </div>

        <!-- Greeting -->
        <h1 class="text-xl font-extrabold mb-2 text-[color:var(--text)]">
          {{ t('phoneTitle') }}
        </h1>
        <p class="text-sm text-[color:var(--muted)] leading-relaxed">
          {{ t('phoneSub') }}
        </p>
      </div>

      <!-- Middle Section: Waiting status or error info -->
      <div class="w-full my-6 flex flex-col justify-center items-center">
        <!-- Error message -->
        <div v-if="error" 
             class="w-full px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-2xl text-xs text-[color:var(--text-error)] text-center font-semibold animate-[scaleIn_0.2s_ease-out]">
          {{ error }}
        </div>

        <!-- Waiting status using card-luxury class -->
        <Transition name="page">
          <div v-if="waiting" class="card-luxury w-full flex items-center justify-center gap-3" style="margin-bottom: 0;">
            <div class="dots-loader flex gap-1.5">
              <span class="w-1.5 h-1.5 rounded-full animate-dot-bounce" style="background-color: var(--gold); animation-delay: 0s;"></span>
              <span class="w-1.5 h-1.5 rounded-full animate-dot-bounce" style="background-color: var(--gold); animation-delay: 0.2s;"></span>
              <span class="w-1.5 h-1.5 rounded-full animate-dot-bounce" style="background-color: var(--gold); animation-delay: 0.4s;"></span>
            </div>
            <p class="text-xs text-[color:var(--muted)] font-bold uppercase tracking-wider">{{ t('confirmChecking') }}</p>
          </div>
        </Transition>
      </div>

      <!-- Bottom Section: Share contact button or Manual Phone form -->
      <div class="w-full">
        <Transition name="page">
          <form v-if="manualInputMode" @submit.prevent="submitManualPhone" class="flex flex-col gap-3">
            <div class="flex flex-col gap-1">
              <input 
                type="tel" 
                v-model="manualPhone" 
                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-2xl text-center tracking-wider font-bold text-lg text-[color:var(--text)] focus:outline-none focus:border-[color:var(--gold)]"
                :placeholder="t('phonePlaceholder') || '+7 (___) ___-__-__'"
              />
              <span v-if="submitError" class="text-xs text-[color:var(--text-error)] text-center">{{ submitError }}</span>
            </div>
            <button
              type="submit"
              :disabled="isSubmitting"
              class="btn-primary w-full mt-2"
            >
              <span v-if="isSubmitting" class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
              <template v-else>
                {{ t('continue') }}
              </template>
            </button>
          </form>

          <button
            v-else
            id="btn-share-contact"
            @click="handleShareContact"
            :disabled="waiting"
            class="btn-primary w-full"
          >
            <span v-if="waiting" class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            <template v-else>
              <svg class="w-5 h-5 fill-current opacity-95" viewBox="0 0 24 24">
                <path d="M19 14v3h3v2h-3v3h-2v-3h-3v-2h3v-3h2zm-9-2c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm0 2c-2.67 0-8 1.34-8 4v3h10.19c-.12-.65-.19-1.32-.19-2 0-2.24 1.28-4.17 3.14-5.14L10 14z"/>
              </svg>
              {{ t('sharePhoneBtn') }}
            </template>
          </button>
        </Transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { requestContact } from '@/services/telegram'
import api from '@/services/api'
import { t } from '@/i18n'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()

const waiting = ref(false)
const error = ref('')

const manualInputMode = ref(false)
const manualPhone = ref('+7')
const submitError = ref('')
const isSubmitting = ref(false)

let ws = null
let pollInterval = null
let fallbackTimer = null

function connectWebSocket() {
  const customerId = auth.customer?.id
  const token = auth.accessToken
  if (!customerId || !token) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/ws/loyalty/user_updates/${customerId}/?token=${token}`

  try {
    ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if ((data?.message?.event === 'phone_updated' || data?.message?.event === 'phone_confirmed') && data.message.phone) {
        auth.updateCustomer({
          phone: data.message.phone,
          is_onboarded: true,
        })
        cleanup()
        if (auth.needsConsent) {
          router.replace('/onboarding/consent')
        } else {
          router.replace('/')
        }
      }
    }

    ws.onerror = () => {
      console.warn('WebSocket error, falling back to polling')
    }
  } catch (e) {
    console.warn('WebSocket connection failed:', e)
  }
}

function startPolling() {
  pollInterval = setInterval(async () => {
    try {
      const res = await api.get('/loyalty/customer/me/')
      if (res.data.phone) {
        auth.updateCustomer({
          phone: res.data.phone,
          is_onboarded: true,
          loyalty_balance: res.data.loyalty_balance,
        })
        cleanup()
        if (auth.needsConsent) {
          router.replace('/onboarding/consent')
        } else {
          router.replace('/')
        }
      }
    } catch {
      // Silently retry
    }
  }, 4000)
}

function cleanup() {
  if (ws) { ws.close(); ws = null }
  if (pollInterval) { clearInterval(pollInterval); pollInterval = null }
  if (fallbackTimer) { clearTimeout(fallbackTimer); fallbackTimer = null }
  waiting.value = false
}

async function handleShareContact() {
  error.value = ''
  waiting.value = true
  manualInputMode.value = false

  // Start polling and websocket listening immediately
  connectWebSocket()
  startPolling()

  // Start 5-second fallback timer
  fallbackTimer = setTimeout(() => {
    if (waiting.value) {
      cleanup()
      manualInputMode.value = true
      error.value = t('phoneFallbackMessage') || 'Не удалось получить номер телефона автоматически. Пожалуйста, введите номер вручную.'
    }
  }, 5000)

  try {
    await requestContact()
  } catch (e) {
    // If user cancelled, clean up background tasks
    cleanup()
    manualInputMode.value = true
    error.value = e.message || t('declinedPhone')
  }
}

async function submitManualPhone() {
  if (!manualPhone.value || manualPhone.value.length < 11) {
    submitError.value = 'Пожалуйста, введите корректный номер'
    return
  }
  
  submitError.value = ''
  isSubmitting.value = true
  
  try {
    const res = await api.post('/loyalty/customer/phone/', { phone: manualPhone.value })
    if (res.data.phone) {
      auth.updateCustomer({
        phone: res.data.phone,
        is_onboarded: true,
        loyalty_balance: res.data.loyalty_balance,
      })
      if (auth.needsConsent) {
        router.replace('/onboarding/consent')
      } else {
        router.replace('/')
      }
    }
  } catch (err) {
    submitError.value = err.response?.data?.error || 'Ошибка при сохранении номера'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(() => {
  // If the user already has a phone registered, redirect them forward
  if (auth.isOnboarded) {
    if (auth.needsConsent) {
      router.replace('/onboarding/consent')
    } else {
      router.replace('/')
    }
  }
})

onUnmounted(cleanup)
</script>
