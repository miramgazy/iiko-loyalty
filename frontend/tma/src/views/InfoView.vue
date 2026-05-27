<template>
  <div class="min-h-screen relative overflow-hidden flex flex-col"
       :style="{ paddingTop: `calc(env(safe-area-inset-top, 0px) + 12px)` }">
    <!-- Dynamic radial glows -->
    <div class="absolute w-[220px] h-[220px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Loading State -->
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-50 bg-[color:var(--bg)]/50 backdrop-blur-sm">
      <div class="w-10 h-10 border-[3px] rounded-full animate-spin"
           :style="{ borderColor: 'var(--gold-glow)', borderTopColor: 'var(--gold)' }"></div>
    </div>

    <!-- Main Content Container with proportional padding and spacing -->
    <div v-else class="flex-grow page-p space-y-4 z-10 relative flex flex-col justify-start overflow-y-auto">
      
      <!-- Top Card: Header Title -->
      <div class="card-luxury text-left shadow-sm" style="margin-bottom: 0;">
        <h1 class="text-xl font-extrabold text-[color:var(--text)]">
          {{ t('info') }}
        </h1>
      </div>

      <!-- Empty State -->
      <div v-if="programs.length === 0" class="text-center py-16 text-[color:var(--muted)] text-sm">
        {{ t('noInfo') }}
      </div>

      <!-- Programs List -->
      <div v-else v-for="prog in programs" :key="prog.id" class="card-luxury text-left flex flex-col shadow-sm" style="margin-bottom: 0;">
        <h3 class="text-base font-extrabold text-[color:var(--gold)] mb-2 uppercase tracking-wide">
          {{ locale === 'kz' && prog.title_kz ? prog.title_kz : prog.title }}
        </h3>
        <p class="text-sm text-[color:var(--text)] leading-relaxed whitespace-pre-wrap font-medium">
          {{ locale === 'kz' && prog.description_kz ? prog.description_kz : prog.description }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'
import { t } from '@/i18n'

const auth = useAuthStore()
const programs = ref([])
const loading = ref(true)

const orgId = computed(() => auth.organization?.id || auth.customer?.organization?.id)

async function loadPrograms() {
  const currentOrgId = orgId.value
  if (!currentOrgId) {
    loading.value = false
    return
  }

  loading.value = true
  try {
    const res = await api.get(`/loyalty/organizations/${currentOrgId}/loyalty-programs/`)
    programs.value = res.data
  } catch (e) {
    console.error('Error fetching loyalty programs:', e)
  } finally {
    loading.value = false
  }
}

watch(orgId, (newOrgId) => {
  if (newOrgId) {
    loadPrograms()
  }
}, { immediate: true })
</script>
