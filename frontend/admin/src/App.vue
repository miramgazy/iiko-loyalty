<template>
  <div class="min-h-screen bg-slate-950 flex">
    <!-- Sidebar -->
    <aside v-if="auth.isAuthenticated && auth.currentOrgId || auth.isSuperAdmin"
      class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
      <!-- Logo -->
      <div class="px-6 py-5 border-b border-slate-800">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span class="text-white text-sm font-bold">L</span>
          </div>
          <span class="font-bold text-white tracking-tight">LoyaltyAdmin</span>
        </div>
      </div>

      <!-- Nav Links -->
      <nav class="flex-1 px-3 py-4 space-y-1">
        <template v-if="auth.isSuperAdmin">
          <RouterLink to="/superadmin" class="nav-link" active-class="nav-link-active">
            <span>🏢</span> Организации
          </RouterLink>
          <RouterLink to="/superadmin/users" class="nav-link" active-class="nav-link-active">
            <span>👥</span> Пользователи
          </RouterLink>
        </template>
        <template v-if="auth.currentOrgId">
          <RouterLink v-if="auth.isOrgManager" to="/admin/settings" class="nav-link" active-class="nav-link-active">
            <span>⚙️</span> Настройки
          </RouterLink>
          <RouterLink v-if="auth.isOrgManager" to="/admin/employees" class="nav-link" active-class="nav-link-active">
            <span>👥</span> Сотрудники
          </RouterLink>
          <RouterLink v-if="auth.isOrgAdmin" to="/admin/customers" class="nav-link" active-class="nav-link-active">
            <span>🎯</span> Клиенты
          </RouterLink>
          <RouterLink v-if="auth.isOrgAdmin" to="/admin/mailings" class="nav-link" active-class="nav-link-active">
            <span>📢</span> Рассылки
          </RouterLink>
        </template>
      </nav>

      <!-- User info + logout -->
      <div class="px-4 py-4 border-t border-slate-800">
        <div v-if="auth.currentMembership" class="mb-2 px-2">
          <p class="text-xs text-slate-500 truncate">{{ auth.currentMembership.organization.name }}</p>
          <p class="text-xs text-indigo-400 font-medium">{{ roleLabel(auth.currentRole) }}</p>
        </div>
        <button
          @click="handleLogout"
          class="w-full text-left px-3 py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors flex items-center gap-2"
        >
          <span>🚪</span> Выйти
        </button>
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-auto">
      <RouterView />
    </main>

    <ToastContainer />
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import ToastContainer from '@/components/ToastContainer.vue'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}

function roleLabel(role) {
  const labels = {
    superuser: 'SuperUser',
    superadmin: 'SuperAdmin',
    org_manager: 'Менеджер',
    org_admin: 'Администратор',
  }
  return labels[role] || role
}
</script>

<style scoped>
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #94a3b8;
  border-radius: 0.5rem;
  transition: all 150ms;
}
.nav-link:hover {
  background-color: rgba(30,41,59,1);
  color: white;
}
.nav-link-active {
  background-color: rgba(99,102,241,0.2);
  color: #a5b4fc;
}
.nav-link-active:hover {
  background-color: rgba(99,102,241,0.3);
  color: #c7d2fe;
}
</style>
