<template>
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-900 rounded-2xl border border-slate-700 w-full max-w-4xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        
        <!-- Header -->
        <div class="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/40">
          <div>
            <div class="flex items-center gap-3">
              <h2 class="text-xl font-bold text-white flex items-center gap-2">
                <span>🖥️</span> Активация терминалов iikoFront
              </h2>
              <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-900/50 text-indigo-300 border border-indigo-700">
                {{ org?.name }}
              </span>
            </div>
            <p class="text-slate-400 text-xs mt-1">
              Управление лицензиями касс, мониторинг связи и синхронизация с iiko
            </p>
            
            <!-- Terminal Secret for Config -->
            <div v-if="terminalSecret" class="mt-3 flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 w-fit">
              <span class="text-[11px] text-slate-400">Ключ терминалов:</span>
              <code class="text-xs font-mono text-amber-300">{{ terminalSecret }}</code>
              <button @click="copySecret" type="button" class="text-xs text-slate-400 hover:text-white ml-1 transition-colors" title="Копировать в конфиг плагина">
                {{ copied ? '✅ Скопировано' : '📋' }}
              </button>
            </div>
          </div>

          <button @click="close" class="text-slate-400 hover:text-white text-xl p-1 rounded-lg transition-colors">
            ✕
          </button>
        </div>

        <!-- Toolbar & Filter Cards -->
        <div class="p-6 pb-2 space-y-4">
          <!-- Stats / Filters -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <button @click="statusFilter = 'all'" 
                    class="p-3 rounded-xl border text-left transition-all"
                    :class="statusFilter === 'all' ? 'border-indigo-500 bg-indigo-950/30' : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'">
              <p class="text-[11px] text-slate-400 uppercase font-semibold">Всего касс</p>
              <p class="text-xl font-bold text-white mt-1">{{ summary.total }}</p>
            </button>
            
            <button @click="statusFilter = 'online'"
                    class="p-3 rounded-xl border text-left transition-all"
                    :class="statusFilter === 'online' ? 'border-emerald-500 bg-emerald-950/30' : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'">
              <p class="text-[11px] text-emerald-400 uppercase font-semibold flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Онлайн
              </p>
              <p class="text-xl font-bold text-white mt-1">{{ summary.online }}</p>
            </button>

            <button @click="statusFilter = 'offline'"
                    class="p-3 rounded-xl border text-left transition-all"
                    :class="statusFilter === 'offline' ? 'border-amber-500 bg-amber-950/30' : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'">
              <p class="text-[11px] text-amber-400 uppercase font-semibold flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-amber-400"></span> Офлайн
              </p>
              <p class="text-xl font-bold text-white mt-1">{{ summary.offline }}</p>
            </button>

            <button @click="statusFilter = 'not_installed'"
                    class="p-3 rounded-xl border text-left transition-all"
                    :class="statusFilter === 'not_installed' ? 'border-red-500 bg-red-950/30' : 'border-slate-800 bg-slate-800/50 hover:border-slate-700'">
              <p class="text-[11px] text-red-400 uppercase font-semibold flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-red-400"></span> Без плагина
              </p>
              <p class="text-xl font-bold text-white mt-1">{{ summary.not_installed }}</p>
            </button>
          </div>

          <!-- Search & Sync Button -->
          <div class="flex items-center justify-between gap-4 pt-1">
            <div class="relative flex-1">
              <input v-model="searchQuery" type="text" placeholder="Поиск кассы по названию или группе..." 
                     class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>

            <button @click="syncWithIiko" :disabled="syncing"
                    class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-lg shadow-indigo-600/20">
              <span :class="{ 'animate-spin': syncing }">🔄</span>
              <span>{{ syncing ? 'Синхронизация...' : 'Запросить из iiko' }}</span>
            </button>
          </div>
        </div>

        <!-- Table container -->
        <div class="flex-1 overflow-y-auto px-6 py-2">
          <div v-if="loading" class="py-16 flex items-center justify-center">
            <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          </div>

          <div v-else-if="filteredTerminals.length === 0" class="py-16 text-center text-slate-500 text-sm">
            <p>Терминалы не найдены</p>
            <p class="text-xs text-slate-600 mt-1">Нажмите «Запросить из iiko», чтобы загрузить кассы ресторана</p>
          </div>

          <table v-else class="w-full text-left border-collapse">
            <thead>
              <tr class="border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400">
                <th class="py-3 px-3 w-8">
                  <input type="checkbox" :checked="isAllSelected" @change="toggleSelectAll"
                         class="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-600" />
                </th>
                <th class="py-3 px-3">Касса / Группа</th>
                <th class="py-3 px-3">Статус плагина</th>
                <th class="py-3 px-3">UUID</th>
                <th class="py-3 px-3 text-right">Лицензия</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 text-xs">
              <tr v-for="t in filteredTerminals" :key="t.id" class="hover:bg-slate-800/30 transition-colors">
                <!-- Checkbox -->
                <td class="py-3 px-3">
                  <input type="checkbox" :value="t.id" v-model="selectedIds"
                         class="rounded border-slate-700 bg-slate-800 text-indigo-600 focus:ring-indigo-600" />
                </td>

                <!-- Name & Group -->
                <td class="py-3 px-3">
                  <p class="font-medium text-white">{{ t.name }}</p>
                  <p v-if="t.group_name" class="text-[11px] text-slate-400 mt-0.5">{{ t.group_name }}</p>
                </td>

                <!-- Plugin status -->
                <td class="py-3 px-3">
                  <div v-if="t.plugin_status === 'online'" class="flex items-center gap-1.5 text-emerald-400">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span class="font-medium">Онлайн</span>
                    <span v-if="t.plugin_version" class="text-[10px] bg-emerald-950/60 border border-emerald-800 text-emerald-300 px-1.5 py-0.2 rounded font-mono">
                      v{{ t.plugin_version }}
                    </span>
                    <span v-if="t.ip_address" class="text-[10px] text-slate-500 font-mono ml-1">({{ t.ip_address }})</span>
                  </div>

                  <div v-else-if="t.plugin_status === 'offline'" class="flex items-center gap-1.5 text-amber-400">
                    <span class="w-2 h-2 rounded-full bg-amber-400"></span>
                    <span>Офлайн</span>
                    <span class="text-[10px] text-slate-500">({{ formatRelativeTime(t.last_seen_at) }})</span>
                  </div>

                  <div v-else class="inline-flex items-center gap-1 text-[11px] text-red-400 bg-red-950/40 border border-red-900/60 px-2 py-0.5 rounded-lg">
                    <span>⚠️ Плагин не установлен</span>
                  </div>
                </td>

                <!-- UUID -->
                <td class="py-3 px-3">
                  <span class="font-mono text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded cursor-pointer hover:text-white"
                        @click="copyText(t.terminal_id)" title="Нажмите, чтобы скопировать">
                    {{ t.terminal_id.slice(0, 8) }}...{{ t.terminal_id.slice(-4) }}
                  </span>
                </td>

                <!-- Toggle switch -->
                <td class="py-3 px-3 text-right">
                  <button @click="toggleTerminal(t)" :disabled="togglingId === t.id"
                          type="button"
                          class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50"
                          :class="t.is_active ? 'bg-emerald-600' : 'bg-slate-700'">
                    <span class="pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
                          :class="t.is_active ? 'translate-x-4' : 'translate-x-0'"></span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Floating Bulk Actions Toolbar -->
        <Transition name="slide-up">
          <div v-if="selectedIds.length > 0"
               class="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-4">
            <span class="text-xs text-slate-300 font-medium">
              Выбрано касс: <b class="text-white">{{ selectedIds.length }}</b>
            </span>
            <div class="flex items-center gap-2">
              <button @click="bulkToggle(true)" :disabled="bulkUpdating"
                      class="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-all">
                Включить выбранные
              </button>
              <button @click="bulkToggle(false)" :disabled="bulkUpdating"
                      class="bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-all">
                Отключить выбранные
              </button>
              <button @click="selectedIds = []" class="text-xs text-slate-400 hover:text-white px-2 py-1">
                Снять выбор
              </button>
            </div>
          </div>
        </Transition>

      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '@/services/api'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  show: Boolean,
  org: Object
})

const emit = defineEmits(['close', 'updated'])
const toast = useToastStore()

const loading = ref(false)
const syncing = ref(false)
const bulkUpdating = ref(false)
const togglingId = ref(null)
const terminals = ref([])
const terminalSecret = ref('')
const selectedIds = ref([])
const statusFilter = ref('all')
const searchQuery = ref('')
const copied = ref(false)

const summary = ref({
  total: 0,
  active_licensed: 0,
  online: 0,
  offline: 0,
  not_installed: 0
})

watch(() => props.show, (newVal) => {
  if (newVal && props.org?.id) {
    loadTerminals()
    selectedIds.value = []
    statusFilter.value = 'all'
    searchQuery.value = ''
  }
})

async function loadTerminals() {
  if (!props.org?.id) return
  loading.value = true
  try {
    const res = await api.get(`/core/superadmin/organizations/${props.org.id}/terminals/`)
    terminals.value = res.data.terminals || []
    summary.value = res.data.summary || summary.value
    terminalSecret.value = res.data.terminal_secret || ''
  } catch (e) {
    toast.error('Не удалось загрузить терминалы организации')
  } finally {
    loading.value = false
  }
}

async function syncWithIiko() {
  if (!props.org?.id) return
  syncing.value = true
  try {
    const res = await api.post(`/core/superadmin/organizations/${props.org.id}/sync-terminals/`)
    toast.success(res.data.message || 'Синхронизация завершена')
    await loadTerminals()
    emit('updated')
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Ошибка синхронизации с iiko Cloud'
    toast.error(errorMsg)
  } finally {
    syncing.value = false
  }
}

async function toggleTerminal(terminal) {
  togglingId.value = terminal.id
  const newActive = !terminal.is_active
  try {
    await api.patch(`/core/superadmin/terminals/${terminal.id}/toggle/`, { is_active: newActive })
    terminal.is_active = newActive
    summary.value.active_licensed += newActive ? 1 : -1
    toast.success(newActive ? `Касса «${terminal.name}» активирована` : `Касса «${terminal.name}» отключена`)
    emit('updated')
  } catch (e) {
    toast.error('Не удалось изменить статус кассы')
  } finally {
    togglingId.value = null
  }
}

async function bulkToggle(isActive) {
  if (selectedIds.value.length === 0) return
  bulkUpdating.value = true
  try {
    await api.post('/core/superadmin/terminals/bulk-toggle/', {
      terminal_ids: selectedIds.value,
      is_active: isActive
    })
    terminals.value.forEach(t => {
      if (selectedIds.value.includes(t.id)) {
        t.is_active = isActive
      }
    })
    selectedIds.value = []
    toast.success(isActive ? 'Выбранные кассы активированы' : 'Выбранные кассы отключены')
    await loadTerminals()
    emit('updated')
  } catch (e) {
    toast.error('Ошибка массового обновления')
  } finally {
    bulkUpdating.value = false
  }
}

const filteredTerminals = computed(() => {
  return terminals.value.filter(t => {
    // Status filter
    if (statusFilter.value !== 'all' && t.plugin_status !== statusFilter.value) {
      return false
    }
    // Search query
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      const nameMatch = (t.name || '').toLowerCase().includes(q)
      const groupMatch = (t.group_name || '').toLowerCase().includes(q)
      const idMatch = (t.terminal_id || '').toLowerCase().includes(q)
      if (!nameMatch && !groupMatch && !idMatch) return false
    }
    return true
  })
})

const isAllSelected = computed(() => {
  if (filteredTerminals.value.length === 0) return false
  return filteredTerminals.value.every(t => selectedIds.value.includes(t.id))
})

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredTerminals.value.map(t => t.id)
  }
}

function copySecret() {
  if (!terminalSecret.value) return
  navigator.clipboard.writeText(terminalSecret.value)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

function copyText(txt) {
  navigator.clipboard.writeText(txt)
  toast.success('Скопировано в буфер обмена')
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

function close() {
  emit('close')
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
