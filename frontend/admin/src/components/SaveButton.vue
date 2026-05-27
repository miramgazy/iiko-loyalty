<template>
  <button
    type="button"
    :disabled="saving"
    @click="$emit('save')"
    class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed
           text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2"
  >
    <span v-if="saving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
    {{ saving ? 'Сохраняем...' : 'Сохранить' }}
  </button>
</template>

<script setup>
defineProps({ saving: Boolean })
defineEmits(['save'])
</script>
