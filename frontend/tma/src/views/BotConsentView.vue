<template>
  <div class="min-h-screen relative overflow-hidden flex flex-col">
    <!-- Background glows -->
    <div class="absolute w-[300px] h-[300px] rounded-full -top-[60px] left-1/2 -translate-x-1/2 pointer-events-none opacity-70"
         style="background: radial-gradient(circle, var(--gold-glow) 0%, transparent 70%);"></div>
    <div class="absolute w-[250px] h-[250px] rounded-full bottom-[100px] -right-[40px] pointer-events-none opacity-40"
         style="background: radial-gradient(circle, var(--gold-glow) 0%, transparent 70%);"></div>

    <!-- Main Content Container matching HomeView layout and padding -->
    <div class="flex-grow page-p z-10 relative flex flex-col justify-between"
         style="padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 24px); padding-top: calc(env(safe-area-inset-top, 0px) + 24px);">

      <!-- Top Section: Logo & Titles -->
      <div class="flex flex-col items-center text-center w-full mt-6">
        <div class="logo-wrap mb-6 flex items-center justify-center relative w-[80px] h-[80px] rounded-[22px] border"
             :style="{ 
               background: `linear-gradient(135deg, var(--gold-glow), rgba(255,255,255,0.02))`,
               borderColor: 'var(--border)'
             }">
          <div class="absolute inset-[-8px] rounded-[30px] bg-[radial-gradient(circle,var(--gold-glow)_0%,transparent_70%)] animate-glow-pulse pointer-events-none"></div>
          <div v-if="theme.logoUrl" class="w-full h-full rounded-[22px] overflow-hidden shadow-xl relative z-10">
            <img :src="theme.logoUrl" alt="Logo" class="w-full h-full object-cover" />
          </div>
          <div v-else class="logo-inner text-3xl font-extrabold tracking-tighter relative z-10 text-[color:var(--gold)]">
            {{ orgName?.[0] || 'L' }}
          </div>
        </div>

        <!-- Icon/Illustration -->
        <div class="text-4xl mb-4 animate-[bounce_2s_infinite]">📢</div>

        <!-- Title & Description -->
        <h1 class="text-xl font-extrabold mb-2 text-[color:var(--text)]">
          {{ t('consentTitle') }}
        </h1>
        <p class="text-sm text-[color:var(--muted)] leading-relaxed">
          {{ t('consentDesc') }}
        </p>
      </div>

      <!-- Middle Section: Benefits / Features list -->
      <div class="w-full my-6 flex flex-col justify-center">
        <!-- Feature items inside card-luxury container -->
        <div class="card-luxury w-full space-y-4 text-left" style="margin-bottom: 0;">
          <div class="flex items-start gap-3">
            <p class="text-xs text-[color:var(--text)] font-semibold leading-normal">{{ t('consentFeature1') }}</p>
          </div>
          <div class="flex items-start gap-3">
            <p class="text-xs text-[color:var(--text)] font-semibold leading-normal">{{ t('consentFeature2') }}</p>
          </div>
          <div class="flex items-start gap-3">
            <p class="text-xs text-[color:var(--text)] font-semibold leading-normal">{{ t('consentFeature3') }}</p>
          </div>
        </div>
      </div>

      <!-- Bottom Section: Buttons -->
      <div class="w-full space-y-3">
        <button
          id="btn-consent-allow"
          @click="handleConsent(true)"
          :disabled="loading"
          class="btn-primary w-full flex items-center justify-center gap-2 active:scale-[0.98] transition-all"
        >
          <span v-if="loading" class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          <template v-else>
            {{ t('consentAllow') }}
          </template>
        </button>

        <button
          id="btn-consent-decline"
          @click="handleConsent(false)"
          :disabled="loading"
          class="w-full py-3.5 rounded-2xl text-sm font-bold transition-all border border-transparent text-[color:var(--muted)] hover:text-[color:var(--text)] active:scale-[0.98] bg-transparent cursor-pointer"
        >
          {{ t('consentDecline') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { t } from '@/i18n'
import api from '@/services/api'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()

const orgName = computed(() => auth.organization?.name || '')
const loading = ref(false)

async function handleConsent(allow) {
  loading.value = true
  try {
    // Save consent response to backend
    await api.patch('/loyalty/customer/me/', {
      is_bot_subscribed: allow
    })

    // Update customer in state
    auth.updateCustomer({
      is_bot_subscribed: allow
    })

    // Redirect to home screen
    router.replace('/')
  } catch (e) {
    console.error('Error saving consent:', e)
    // Fallback: still redirect
    auth.updateCustomer({
      is_bot_subscribed: allow
    })
    router.replace('/')
  } finally {
    loading.value = false
  }
}
</script>
