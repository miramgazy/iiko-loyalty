<template>
  <div class="min-h-screen relative overflow-hidden flex flex-col">
    <!-- Dynamic radial glows -->
    <div class="absolute w-[220px] h-[220px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Main Content Container with proportional padding and spacing -->
    <div class="flex-1 page-p space-y-4 z-10 relative flex flex-col justify-start">
      
      <!-- Second Block: 3D Loyalty Card -->
      <div class="card-luxury flex flex-col justify-between shadow-2xl relative overflow-hidden h-[240px] p-5 text-left select-none"
           :style="{ background: 'var(--gold-gradient)', color: 'var(--gold-text)', borderColor: 'rgba(255,255,255,0.1)' }">
        <!-- Shiny element for premium card feeling -->
        <div class="absolute top-0 -left-[60%] w-[50%] h-full bg-gradient-to-r from-transparent via-white/15 to-transparent skew-x-[-20deg] animate-card-shine pointer-events-none"></div>

        <!-- Top row: Owner Name & Branding Icon -->
        <div class="flex justify-between items-start z-10">
          <div class="flex flex-col text-left">
            <span class="text-[9px] opacity-75 uppercase tracking-wider font-extrabold mb-1">
              {{ t('cardOwner') }}
            </span>
            <span class="text-[17px] font-extrabold tracking-tight leading-none truncate max-w-[200px] mb-1">
              {{ customerName }}
            </span>
            <span class="text-[11px] opacity-80 font-semibold tracking-wider font-mono">
              {{ auth.customer?.phone || '' }}
            </span>
          </div>
          
          <!-- Small branding logo/icon -->
          <div class="w-12 h-12 rounded-xl overflow-hidden bg-white/10 border border-white/10 flex items-center justify-center p-0.5 flex-shrink-0">
            <img v-if="theme.logoUrl" :src="theme.logoUrl" alt="Logo" class="w-full h-full object-contain" />
            <span v-else class="text-sm font-black">{{ orgName?.[0] || 'L' }}</span>
          </div>
        </div>

        <!-- Middle row: Balance & Refresh button -->
        <div class="flex justify-between items-center z-10 my-auto">
          <div class="flex flex-col">
            <span class="text-[9px] opacity-75 uppercase tracking-wider font-bold mb-0.5">
              {{ t('cardBalanceLabel') }}
            </span>
            <div class="flex items-baseline gap-1">
              <span class="text-2xl font-black tracking-tight leading-none">
                {{ formattedPoints }}
              </span>
              <span class="text-[10px] font-bold uppercase tracking-wider opacity-75">{{ t('points') }}</span>
            </div>
          </div>

          <!-- Sync/Refresh balance button inside card -->
          <button @click="syncBalance" 
                  :disabled="isSyncing" 
                  class="w-[32px] h-[32px] rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 flex items-center justify-center text-inherit cursor-pointer transition-all duration-300 active:scale-90 shadow-sm"
                  :class="{ 'spinning': isSyncing }">
            <span v-if="isSyncing" class="inline-block w-3.5 h-3.5 border-2 border-current/30 border-t-current rounded-full animate-spin"></span>
            <svg v-else class="w-3.5 h-3.5 stroke-current" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
            </svg>
          </button>
        </div>

        <!-- Bottom row: Card Number (Left) & QR Code Thumbnail (Right) -->
        <div class="flex justify-between items-end z-10">
          <!-- Card Number & Copy action -->
          <div class="flex flex-col text-left">
            <span class="text-[9px] opacity-75 uppercase tracking-wider font-bold mb-1">
              {{ t('cardNumber') }}
            </span>
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs font-bold tracking-wider">
                {{ qrLabel }}
              </span>
              <button @click="copyId" 
                      class="px-2 py-0.5 text-[9px] font-bold rounded bg-white/10 hover:bg-white/20 active:scale-95 border border-white/10 text-inherit cursor-pointer transition-all duration-200">
                {{ isCopied ? t('copied') : t('copy') }}
              </button>
            </div>
          </div>

          <!-- Clickable QR Code Thumbnail -->
          <div @click="toggleQrZoom(true)" 
               class="w-[80px] h-[80px] bg-white rounded-xl flex items-center justify-center relative p-1 shadow-md cursor-pointer hover:scale-105 active:scale-95 transition-all duration-200">
            <!-- Animated scanner frame border -->
            <div class="qr-frame absolute inset-[-2px] rounded-[10px] border border-transparent animate-qr-pulse"
                 style="background: linear-gradient(135deg, var(--gold-text), transparent, var(--gold-text)) border-box;
                        -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
                        -webkit-mask-composite: destination-out; mask-composite: exclude;"></div>
            <QrcodeVue
              :value="qrContent"
              :size="72"
              level="M"
              render-as="svg"
              :margin="0"
              class="w-[72px] h-[72px]"
            />
          </div>
        </div>
      </div>

      <!-- Wallets Section (shown only when there are multiple wallets) -->
      <div v-if="wallets.length > 1" class="flex flex-col gap-3">
        <span class="text-[10px] tracking-[0.12em] uppercase text-[color:var(--muted)] font-extrabold px-1">
          {{ t('loyaltyPrograms') }}
        </span>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="wallet in wallets"
            :key="wallet.wallet_id || wallet.id"
            class="card-luxury flex flex-col p-4 text-left relative overflow-hidden"
            style="margin: 0;"
          >
            <!-- Subtle glow accent -->
            <div class="absolute top-0 right-0 w-[80px] h-[80px] rounded-full pointer-events-none opacity-10"
                 style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%); transform: translate(30px, -30px);"></div>
            <span class="text-[9px] uppercase tracking-wider text-[color:var(--muted)] font-bold mb-2 truncate z-10">
              {{ wallet.name || t('wallet') }}
            </span>
            <div class="flex items-baseline gap-1 z-10">
              <span class="text-xl font-black tracking-tight text-[color:var(--text)] leading-none">
                {{ Number(wallet.balance).toLocaleString('ru-RU') }}
              </span>
              <span class="text-[9px] font-bold uppercase tracking-wider text-[color:var(--muted)]">pts</span>
            </div>
            <!-- Type badge -->
            <span v-if="wallet.wallet_type === 1"
                  class="mt-2 self-start text-[9px] px-1.5 py-0.5 rounded-full font-semibold z-10"
                  style="background: rgba(201,168,76,0.15); color: var(--gold); border: 1px solid rgba(201,168,76,0.3);">
              {{ t('bonus') }}
            </span>
            <span v-else
                  class="mt-2 self-start text-[9px] px-1.5 py-0.5 rounded-full font-semibold z-10"
                  style="background: rgba(100,130,255,0.12); color: #818cf8; border: 1px solid rgba(100,130,255,0.25);">
              {{ t('coupon') }}
            </span>
          </div>
        </div>
      </div>

      <!-- Status Tier Section -->
      <div class="card-luxury flex flex-col text-left shadow-sm" style="margin-bottom: 0;">
        <!-- Title and Cashback badge -->
        <div class="flex justify-between items-center">
          <div class="flex flex-col">
            <span class="text-[10px] tracking-[0.12em] uppercase text-[color:var(--muted)] font-extrabold mb-1">
              {{ t('participantLabel') }}
            </span>
            <span class="text-[18px] font-extrabold text-[color:var(--text)] leading-tight">
              {{ categoryInfo.displayName }}
            </span>
          </div>
          <!-- Premium Glassmorphic Cashback badge -->
          <div class="cashback-badge px-3 py-1 rounded-xl border flex flex-col items-center justify-center font-bold"
               :style="{
                 background: 'linear-gradient(135deg, rgba(201, 168, 76, 0.15) 0%, rgba(201, 168, 76, 0.05) 100%)',
                 borderColor: 'rgba(201, 168, 76, 0.3)',
                 color: 'var(--gold)'
               }">
            <span class="text-[9px] uppercase tracking-wider leading-none opacity-80 mb-0.5">{{ t('cashbackLabel') }}</span>
            <span class="text-[14px] font-extrabold leading-none">{{ categoryInfo.cashback }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- QR Code Full-Screen Overlay Modal -->
    <Transition name="fade">
      <div v-if="isQrZoomed" 
           class="fixed inset-0 bg-black/85 backdrop-blur-xl z-50 flex flex-col items-center justify-center p-6 select-none"
           @click.self="toggleQrZoom(false)">
        
        <!-- Premium pass container -->
        <div class="bg-[color:var(--bg)] border border-[color:var(--border)] rounded-3xl p-6 shadow-2xl flex flex-col items-center justify-center w-full max-w-[300px] relative animate-[scaleIn_0.25s_ease-out] gap-5"
             style="box-shadow: 0 0 40px rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(255, 255, 255, 0.05) inset;">
          
          <!-- Top Accent Line (Gold) -->
          <div class="w-12 h-1.5 rounded-full" style="background: var(--gold-gradient);"></div>
          
          <div class="text-center">
            <h3 class="text-[12px] tracking-[0.15em] uppercase text-[color:var(--gold)] font-bold mb-1">
              {{ t('showAtCashier') }}
            </h3>
            <p class="text-[10px] text-[color:var(--muted)] max-w-[240px] leading-tight font-medium mx-auto">
              {{ t('qrScanMsg') }}
            </p>
          </div>
          
          <!-- QR Wrapper with scanner effect -->
          <div class="relative p-3 bg-white rounded-2xl shadow-inner border border-zinc-100">
            <!-- Corner glow highlights -->
            <div class="absolute -inset-[2px] rounded-[18px] border border-transparent pointer-events-none"
                 style="background: linear-gradient(135deg, var(--gold), transparent 60%, var(--gold)) border-box;
                        -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
                        -webkit-mask-composite: destination-out; mask-composite: exclude; opacity: 0.7;"></div>
            <QrcodeVue
              :value="qrContent"
              :size="200"
              level="H"
              render-as="svg"
              :margin="0"
              class="w-[200px] h-[200px] block"
            />
          </div>
          
          <!-- Card Label & User Info -->
          <div class="text-center w-full">
            <span class="font-mono text-sm text-[color:var(--text)] font-extrabold tracking-wider block mb-1">
              {{ qrLabel }}
            </span>
            <span class="text-[10px] text-[color:var(--muted)] font-bold tracking-wide uppercase">
              {{ customerName }}
            </span>
          </div>

          <!-- Integrated Close Button in Pass card -->
          <button @click="toggleQrZoom(false)" 
                  class="w-full py-3.5 rounded-2xl bg-[color:var(--bg-secondary)] hover:opacity-90 text-[color:var(--text)] font-extrabold text-sm transition-all duration-200 active:scale-95 border border-[color:var(--border)] cursor-pointer">
            {{ t('close') }}
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import QrcodeVue from 'qrcode.vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import api from '@/services/api'
import { t } from '@/i18n'

const auth = useAuthStore()
const theme = useThemeStore()

// Native Telegram Haptic Feedback caller
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

const customerName = computed(() => {
  const c = auth.customer
  if (!c) return t('guest')
  return [c.first_name, c.last_name].filter(Boolean).join(' ') || t('guest')
})

const customerInitials = computed(() => {
  const c = auth.customer
  return ((c?.first_name?.[0] || '') + (c?.last_name?.[0] || '')).toUpperCase() || '?'
})

const orgName = computed(() => auth.organization?.name || auth.customer?.organization?.name || '')

const pointsBalance = computed(() => auth.customer?.loyalty_balance || 0)

// Wallets from multi-wallet support
const wallets = computed(() => auth.customer?.wallets || [])

// Extract the active category name from iiko customer categories list
const activeCategoryName = computed(() => {
  const categories = auth.customer?.iiko_categories
  if (Array.isArray(categories) && categories.length > 0) {
    const active = categories.find(cat => cat.isActive)
    return active ? active.name : categories[0].name
  }
  return 'new_user'
})

// Match active category to Display Names, Cashback %, and Next Tier Thresholds
const categoryInfo = computed(() => {
  const name = (activeCategoryName.value || '').toLowerCase()
  
  if (name.includes('silver') || name.includes('серебр')) {
    return {
      displayName: t('silverStatus'),
      cashback: 10,
      nextTierName: 'Gold',
      nextTierThreshold: 1500,
      prevTierThreshold: 500,
    }
  } else if (name.includes('gold') || name.includes('золот')) {
    return {
      displayName: t('goldStatus'),
      cashback: 15,
      nextTierName: 'Platinum',
      nextTierThreshold: 5000,
      prevTierThreshold: 1500,
    }
  } else if (name.includes('platinum') || name.includes('платин')) {
    return {
      displayName: t('platinumStatus'),
      cashback: 20,
      nextTierName: null,
      nextTierThreshold: null,
      prevTierThreshold: 5000,
    }
  } else {
    // Default fallback (new_user / Новичок)
    let display = t('newUser')
    if (activeCategoryName.value && activeCategoryName.value !== 'new_user') {
      display = activeCategoryName.value.charAt(0).toUpperCase() + activeCategoryName.value.slice(1)
    }
    return {
      displayName: display,
      cashback: 5,
      nextTierName: 'Silver',
      nextTierThreshold: 500,
      prevTierThreshold: 0,
    }
  }
})


// Point counting micro-animation
const displayedPoints = ref(0)
const formattedPoints = computed(() => {
  const pts = Number(displayedPoints.value)
  if (isNaN(pts)) return '0'
  if (Math.abs(pts - Math.round(pts)) < 0.01) {
    return Math.round(pts).toLocaleString('ru-RU')
  }
  return pts.toLocaleString('ru-RU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
})

function animatePoints(target) {
  const start = displayedPoints.value
  const duration = 1000 // ms
  let startTime = null

  const step = (timestamp) => {
    if (!startTime) startTime = timestamp
    const progress = Math.min((timestamp - startTime) / duration, 1)
    const ease = 1 - Math.pow(1 - progress, 3) // cubic ease-out
    displayedPoints.value = Math.round(start + ease * (target - start))
    if (progress < 1) {
      requestAnimationFrame(step)
    } else {
      displayedPoints.value = target
    }
  }
  requestAnimationFrame(step)
}

watch(pointsBalance, (newVal) => {
  animatePoints(newVal)
})

const qrContent = computed(() => {
  return auth.customer?.iiko_card_number || auth.customer?.iiko_customer_id || auth.customer?.phone || ''
})

const qrLabel = computed(() => {
  if (auth.customer?.iiko_card_number) return auth.customer.iiko_card_number
  if (auth.customer?.iiko_customer_id) return `ID: ${auth.customer.iiko_customer_id.substring(0, 12)}`
  return auth.customer?.phone || ''
})

const isSyncing = ref(false)

async function syncBalance() {
  if (isSyncing.value) return
  isSyncing.value = true
  triggerHaptic('impact', 'light')
  try {
    const res = await api.post('/loyalty/customer/sync/')
    auth.updateCustomer(res.data)
    triggerHaptic('notification', 'success')
  } catch (e) {
    // silent fail
  } finally {
    isSyncing.value = false
  }
}


const isCopied = ref(false)

function copyId() {
  if (isCopied.value) return
  const idToCopy = auth.customer?.iiko_customer_id || auth.customer?.phone || ''
  if (!idToCopy) return
  
  navigator.clipboard.writeText(idToCopy).then(() => {
    isCopied.value = true
    triggerHaptic('notification', 'success')
    setTimeout(() => {
      isCopied.value = false
    }, 1500)
  }).catch(() => {
    // fallback
  })
}


// Full-screen expandable QR code state
const isQrZoomed = ref(false)

function toggleQrZoom(visible) {
  isQrZoomed.value = visible
  if (visible) {
    triggerHaptic('impact', 'medium')
  } else {
    triggerHaptic('impact', 'light')
  }
}

onMounted(async () => {
  // Initialize points animation with current balance
  displayedPoints.value = 0
  animatePoints(pointsBalance.value)
  
  // Triggers light haptic physical feedback on app mount
  triggerHaptic('impact', 'light')

  // Automatically sync balance from iiko on app load
  if (auth.customer?.phone) {
    await syncBalance()
  } else {
    // Fallback if no phone
    try {
      const res = await api.get('/loyalty/customer/me/')
      auth.updateCustomer(res.data)
    } catch {
      // silent
    }
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
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
</style>

