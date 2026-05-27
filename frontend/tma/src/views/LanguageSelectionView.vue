<template>
  <div class="min-h-screen relative overflow-hidden flex flex-col">
    <!-- Background glows -->
    <div class="absolute w-[300px] h-[300px] rounded-full -top-[60px] left-1/2 -translate-x-1/2 pointer-events-none opacity-70"
         style="background: radial-gradient(circle, var(--gold-glow) 0%, transparent 70%);"></div>
    <div class="absolute w-[200px] h-[200px] rounded-full bottom-[40px] -right-[40px] pointer-events-none opacity-40"
         style="background: radial-gradient(circle, var(--gold-glow) 0%, transparent 70%);"></div>

    <!-- Main Content Container matching HomeView layout and padding -->
    <div class="flex-grow page-p z-10 relative flex flex-col justify-between"
         style="padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 24px); padding-top: calc(env(safe-area-inset-top, 0px) + 24px);">
      
      <!-- Top Section: Logo, Title, Description -->
      <div class="flex flex-col items-center text-center w-full mt-4">
        <!-- Logo -->
        <div class="logo-wrap animate-logo-pulse mb-6 flex items-center justify-center relative w-[84px] h-[84px] rounded-[22px] border"
             :style="{ 
               background: `linear-gradient(135deg, var(--gold-glow), rgba(255,255,255,0.02))`,
               borderColor: 'var(--border)'
             }">
          <!-- Pulse glow rings -->
          <div class="absolute inset-[-8px] rounded-[30px] bg-[radial-gradient(circle,var(--gold-glow)_0%,transparent_70%)] animate-glow-pulse pointer-events-none"></div>
          
          <div v-if="theme.logoUrl" class="w-full h-full rounded-[22px] overflow-hidden shadow-xl relative z-10">
            <img :src="theme.logoUrl" alt="Logo" class="w-full h-full object-cover" />
          </div>
          <div v-else class="logo-inner text-3xl font-extrabold tracking-tighter relative z-10 text-[color:var(--gold)]">
            {{ orgName?.[0] || 'L' }}
          </div>
        </div>

        <!-- Title & Description (Bilingual) -->
        <h1 class="text-xl font-extrabold mb-2 text-[color:var(--text)]">
          {{ t('selectLanguageTitle') }}
        </h1>
        <p class="text-sm text-[color:var(--muted)] leading-relaxed">
          {{ t('selectLanguageDesc') }}
        </p>
      </div>

      <!-- Middle Section: Language selection buttons -->
      <div class="w-full my-6 flex flex-col justify-center">
        <div class="space-y-3">
          <!-- Russian option -->
          <button 
            @click="selectLanguage('ru')"
            class="card-luxury w-full py-4 px-5 text-left transition-all duration-300 active:scale-[0.98] flex items-center gap-4 relative overflow-hidden cursor-pointer"
            :style="{
              borderColor: selectedLanguage === 'ru' ? 'var(--gold)' : 'var(--border)',
              background: selectedLanguage === 'ru' ? 'var(--brand-10)' : 'var(--card-bg)',
              boxShadow: selectedLanguage === 'ru' ? '0 0 18px var(--gold-glow)' : 'none',
              marginBottom: '0'
            }"
          >
            <div v-if="selectedLanguage === 'ru'" class="absolute inset-0 bg-[linear-gradient(120deg,var(--brand-10)_0%,transparent_60%)] pointer-events-none"></div>
            <span class="flag text-3xl leading-none">🇷🇺</span>
            <div class="lang-info flex-1">
              <div class="lang-name font-bold text-[16px] text-[color:var(--text)]">Русский</div>
              <div class="lang-native text-[12px] font-semibold text-[color:var(--muted)]">Russian</div>
            </div>
            <div 
              class="radio-dot w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200 flex-shrink-0"
              :style="{
                borderColor: selectedLanguage === 'ru' ? 'var(--gold)' : 'var(--border)',
                backgroundColor: selectedLanguage === 'ru' ? 'var(--gold)' : 'transparent'
              }"
            >
              <div class="radio-check w-2 h-2 rounded-full transition-transform duration-200"
                   :style="{ 
                     transform: selectedLanguage === 'ru' ? 'scale(1)' : 'scale(0)',
                     backgroundColor: 'var(--gold-text)'
                   }"></div>
            </div>
          </button>

          <!-- Kazakh option -->
          <button 
            @click="selectLanguage('kz')"
            class="card-luxury w-full py-4 px-5 text-left transition-all duration-300 active:scale-[0.98] flex items-center gap-4 relative overflow-hidden cursor-pointer"
            :style="{
              borderColor: selectedLanguage === 'kz' ? 'var(--gold)' : 'var(--border)',
              background: selectedLanguage === 'kz' ? 'var(--brand-10)' : 'var(--card-bg)',
              boxShadow: selectedLanguage === 'kz' ? '0 0 18px var(--gold-glow)' : 'none',
              marginBottom: '0'
            }"
          >
            <div v-if="selectedLanguage === 'kz'" class="absolute inset-0 bg-[linear-gradient(120deg,var(--brand-10)_0%,transparent_60%)] pointer-events-none"></div>
            <span class="flag text-3xl leading-none">🇰🇿</span>
            <div class="lang-info flex-1">
              <div class="lang-name font-bold text-[16px] text-[color:var(--text)]">Қазақша</div>
              <div class="lang-native text-[12px] font-semibold text-[color:var(--muted)]">Kazakh</div>
            </div>
            <div 
              class="radio-dot w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all duration-200 flex-shrink-0"
              :style="{
                borderColor: selectedLanguage === 'kz' ? 'var(--gold)' : 'var(--border)',
                backgroundColor: selectedLanguage === 'kz' ? 'var(--gold)' : 'transparent'
              }"
            >
              <div class="radio-check w-2 h-2 rounded-full transition-transform duration-200"
                   :style="{ 
                     transform: selectedLanguage === 'kz' ? 'scale(1)' : 'scale(0)',
                     backgroundColor: 'var(--gold-text)'
                   }"></div>
            </div>
          </button>
        </div>
      </div>

      <!-- Bottom Section: Continue button -->
      <div class="w-full">
        <button
          id="btn-continue-lang"
          @click="handleContinue"
          :disabled="saving"
          class="btn-primary w-full group"
        >
          <span v-if="saving" class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          <template v-else>
            {{ t('continue') }}
            <span class="transition-transform duration-200 group-hover:translate-x-1">→</span>
          </template>
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
import { t, setLocale } from '@/i18n'
import api from '@/services/api'
import { safeStorage } from '@/services/storage'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()

const orgName = computed(() => auth.organization?.name || '')

const selectedLanguage = ref(auth.customer?.language || 'ru')
const saving = ref(false)

function selectLanguage(lang) {
  selectedLanguage.value = lang
  setLocale(lang)
}

async function handleContinue() {
  saving.value = true
  try {
    // 1. Save language choice to backend
    await api.patch('/loyalty/customer/me/', {
      language: selectedLanguage.value
    })
    
    // 2. Update client auth store state
    auth.updateCustomer({
      language: selectedLanguage.value
    })

    // 3. Mark language as selected for onboarding redirection logic
    safeStorage.setItem('tma_lang_selected', 'true')
    
    // 4. Redirect to phone input view
    router.replace('/onboarding/phone')
  } catch (e) {
    console.error('Error saving language:', e)
    // Fallback: still navigate if API fails
    safeStorage.setItem('tma_lang_selected', 'true')
    router.replace('/onboarding/phone')
  } finally {
    saving.value = false
  }
}
</script>
