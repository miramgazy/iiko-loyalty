<template>
  <div class="min-h-screen flex items-center justify-center bg-slate-950 px-4">
    <div class="w-full max-w-lg">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-white">Выберите организацию</h1>
        <p class="text-slate-400 text-sm mt-1">Выберите ресторан для управления</p>
      </div>
      <div class="space-y-3">
        <button
          v-for="m in auth.user?.memberships"
          :key="m.organization.id"
          id="btn-select-org"
          @click="select(m)"
          class="w-full bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-indigo-500
                 rounded-2xl p-5 text-left transition-all duration-200 group"
        >
          <div class="flex items-center justify-between">
            <div>
              <p class="font-semibold text-white group-hover:text-indigo-300 transition-colors">
                {{ m.organization.name }}
              </p>
              <p class="text-xs text-slate-500 mt-0.5">
                {{ roleLabel(m.role) }} · {{ m.organization.slug }}
              </p>
            </div>
            <span class="text-slate-600 group-hover:text-indigo-400 transition-colors text-xl">→</span>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function select(membership) {
  auth.setCurrentOrg(membership.organization.id)
  router.push('/admin/customers')
}

function roleLabel(role) {
  return { org_manager: 'Менеджер', org_admin: 'Администратор' }[role] || role
}
</script>
