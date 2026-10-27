<template>
  <div class="min-h-screen bg-slate-950 flex">
    <!-- Sidebar -->
    <aside v-if="auth.isAuthenticated && auth.currentOrgId || auth.isSuperAdmin"
      class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
      <!-- Organization / Brand Header -->
      <div class="px-6 py-5 border-b border-slate-800">
        <div class="flex items-center gap-3 min-w-0">
          <div class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
            <span class="text-white text-sm font-bold">{{ currentCompanyInitial }}</span>
          </div>
          <span class="font-bold text-white tracking-tight truncate" :title="currentCompanyName">
            {{ currentCompanyName }}
          </span>
        </div>
      </div>

      <!-- Nav Links -->
      <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <template v-if="auth.isSuperAdmin">
          <RouterLink to="/superadmin" @click="closeSettings" class="nav-link" active-class="nav-link-active">
            <span>🏢</span> Организации
          </RouterLink>
          <RouterLink to="/superadmin/users" @click="closeSettings" class="nav-link" active-class="nav-link-active">
            <span>👥</span> Пользователи
          </RouterLink>
        </template>
        <template v-if="auth.currentOrgId">
          <!-- Dynamic Collapsible Settings Menu -->
          <div v-if="auth.isOrgManager" class="space-y-1">
            <button
              type="button"
              id="sidebar-nav-settings"
              @click="toggleSettings"
              class="w-full nav-link justify-between cursor-pointer group select-none text-left"
              :class="{
                'nav-link-active': isSettingsRoute,
                'text-white bg-slate-800/60': isSettingsOpen && !isSettingsRoute
              }"
            >
              <div class="flex items-center gap-3 min-w-0">
                <span class="text-base flex-shrink-0">⚙️</span>
                <span class="truncate">Настройки</span>
              </div>
              <svg
                class="w-4 h-4 text-slate-400 group-hover:text-slate-200 transition-transform duration-200 flex-shrink-0 mr-1"
                :class="{ 'rotate-90 text-indigo-400': isSettingsOpen }"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>

            <!-- Submenu Items -->
            <div
              v-show="isSettingsOpen"
              class="pl-3 py-1 space-y-0.5 border-l border-slate-800 ml-4 my-1 transition-all duration-200"
            >
              <RouterLink
                v-for="subTab in settingsSubTabs"
                :key="subTab.id"
                :id="`sidebar-subtab-${subTab.id}`"
                :to="{ path: '/admin/settings', query: { tab: subTab.id } }"
                class="subnav-link group"
                :class="{
                  'subnav-link-active': isSettingsRoute && activeSettingsTab === subTab.id
                }"
              >
                <span class="text-xs flex-shrink-0 opacity-80 group-hover:opacity-100">{{ subTab.icon }}</span>
                <span class="truncate text-xs">{{ subTab.label }}</span>
              </RouterLink>
            </div>
          </div>

          <RouterLink v-if="auth.isOrgManager" to="/admin/employees" @click="closeSettings" class="nav-link" active-class="nav-link-active">
            <span>👥</span> Сотрудники
          </RouterLink>
          <RouterLink v-if="auth.isOrgManager" to="/admin/tma-employees" @click="closeSettings" class="nav-link" active-class="nav-link-active">
            <span>👥</span> Персонал TMA
          </RouterLink>

          <!-- Loyalty Module Links -->
          <template v-if="auth.currentMembership?.organization?.is_loyalty_enabled">
            <RouterLink v-if="auth.isOrgAdmin" to="/admin/customers" @click="closeSettings" class="nav-link" active-class="nav-link-active">
              <span>🎯</span> Клиенты
            </RouterLink>
            <RouterLink v-if="auth.isOrgAdmin" to="/admin/mailings" @click="closeSettings" class="nav-link" active-class="nav-link-active">
              <span>📢</span> Рассылки
            </RouterLink>
          </template>

          <!-- Analytics & Inventory Module Links -->
          <template v-if="auth.currentMembership?.organization?.is_analytics_enabled">
            <RouterLink to="/admin/analytics" @click="closeSettings" class="nav-link" active-class="nav-link-active">
              <span>📊</span> Аналитика
            </RouterLink>
            <RouterLink to="/admin/inventory" @click="closeSettings" class="nav-link" active-class="nav-link-active">
              <span>📦</span> Закупки & Min-Max
            </RouterLink>
          </template>

          <!-- AI Agent Module Links -->
          <template v-if="auth.currentMembership?.organization?.is_ai_agent_enabled">
            <RouterLink to="/admin/ai-agent" @click="closeSettings" class="nav-link" active-class="nav-link-active">
              <span>🤖</span> Чат с AI
            </RouterLink>
          </template>
        </template>
      </nav>

      <!-- User info + logout -->
      <div class="px-4 py-4 border-t border-slate-800">
        <div class="mb-2 px-2">
          <p class="text-xs text-slate-300 font-medium truncate">
            {{ auth.user?.first_name || auth.user?.username || 'Пользователь' }}
          </p>
          <p class="text-xs text-indigo-400 font-medium">{{ roleLabel(auth.currentRole) }}</p>
          <RouterLink
            v-if="auth.user?.memberships?.length > 1"
            to="/select-org"
            class="inline-block mt-1 text-[11px] text-slate-500 hover:text-indigo-400 transition-colors"
          >
            ⇄ Сменить организацию
          </RouterLink>
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
import { ref, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import ToastContainer from '@/components/ToastContainer.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const isSettingsOpen = ref(false)
const isSettingsRoute = computed(() => route.path === '/admin/settings')
const activeSettingsTab = computed(() => (route.query.tab ? String(route.query.tab) : 'general'))

const settingsSubTabs = computed(() => {
  const org = auth.currentMembership?.organization
  const list = [
    { id: 'general', label: 'Основные / Telegram', icon: '⚙️' },
    { id: 'waba', label: 'Настройка WABA', icon: '💬' },
    { id: 'iiko', label: 'Интеграция iiko Cloud API', icon: '☁️' },
    { id: 'iiko_server', label: 'Интеграция iiko Server API', icon: '🖥️' },
  ]
  if (org?.is_loyalty_enabled) {
    list.push(
      { id: 'card_tiers', label: 'Ранги и дизайн карт', icon: '💳' },
      { id: 'onboarding', label: 'Страница онбординга', icon: '🚀' },
      { id: 'branding', label: 'Брендинг TMA', icon: '🎨' },
      { id: 'wallet', label: 'Google Wallet', icon: '🌐' },
      { id: 'apple_wallet', label: 'Apple Wallet', icon: '🍏' },
      { id: 'loyalty_programs', label: 'Программа лояльности', icon: '🎁' }
    )
  }
  if (org?.is_ai_agent_enabled) {
    list.push({ id: 'llm', label: 'Настройки LLM', icon: '🤖' })
  }
  return list
})

watch(() => route.path, (newPath) => {
  if (newPath === '/admin/settings') {
    isSettingsOpen.value = true
  } else {
    isSettingsOpen.value = false
  }
}, { immediate: true })

function toggleSettings() {
  if (!isSettingsOpen.value) {
    isSettingsOpen.value = true
    router.push({ path: '/admin/settings', query: { tab: 'general' } })
  } else if (!isSettingsRoute.value) {
    router.push({ path: '/admin/settings', query: { tab: 'general' } })
  } else {
    if (activeSettingsTab.value !== 'general') {
      router.push({ path: '/admin/settings', query: { tab: 'general' } })
    } else {
      isSettingsOpen.value = false
    }
  }
}

function closeSettings() {
  isSettingsOpen.value = false
}

const currentCompanyName = computed(() => {
  return auth.currentMembership?.organization?.name || (auth.isSuperAdmin ? 'Панель управления' : 'Loyalty-MadiTech')
})

const currentCompanyInitial = computed(() => {
  const name = currentCompanyName.value.trim()
  return name ? name.charAt(0).toUpperCase() : 'L'
})

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
  if (!role && auth.isSuperAdmin) return 'SuperAdmin'
  return labels[role] || role || ''
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

.subnav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.625rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: #94a3b8;
  border-radius: 0.5rem;
  transition: all 150ms;
}
.subnav-link:hover {
  background-color: rgba(30, 41, 59, 0.7);
  color: #f1f5f9;
}
.subnav-link-active {
  background-color: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
  font-weight: 600;
}
.subnav-link-active:hover {
  background-color: rgba(99, 102, 241, 0.3);
  color: #c7d2fe;
}
</style>
