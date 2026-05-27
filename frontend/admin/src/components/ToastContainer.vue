<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toastStore.toasts"
          :key="toast.id"
          class="flex items-start gap-3 p-4 rounded-xl shadow-2xl border cursor-pointer"
          :class="toastClass(toast.type)"
          @click="toastStore.dismiss(toast.id)"
        >
          <span class="text-lg flex-shrink-0">{{ toastIcon(toast.type) }}</span>
          <p class="text-sm font-medium leading-snug">{{ toast.message }}</p>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'
const toastStore = useToastStore()

const toastClass = (type) => ({
  'bg-emerald-950 border-emerald-700 text-emerald-100': type === 'success',
  'bg-red-950 border-red-700 text-red-100': type === 'error',
  'bg-slate-800 border-slate-600 text-slate-100': type === 'info',
})

const toastIcon = (type) => ({ success: '✅', error: '❌', info: 'ℹ️' }[type] || 'ℹ️')
</script>
