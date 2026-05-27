<template>
  <div class="p-8 text-slate-100">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold text-white tracking-tight">Telegram Рассылки</h1>
        <p class="text-slate-400 text-sm mt-1">Создание и аналитика маркетинговых кампаний в Telegram-боте</p>
      </div>
      <button
        id="btn-create-mailing"
        @click="openCreateModal"
        class="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-3 rounded-xl text-sm transition-all shadow-lg hover:shadow-indigo-500/20 active:scale-95 flex items-center gap-2"
      >
        <span>➕</span> Создать рассылку
      </button>
    </div>

    <!-- Stats summary -->
    <div class="grid grid-cols-4 gap-6 mb-8">
      <div v-for="stat in generalStats" :key="stat.label" class="bg-slate-900 rounded-2xl border border-slate-800 p-6 flex flex-col justify-between shadow-sm">
        <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ stat.label }}</span>
        <span class="text-3xl font-extrabold text-white mt-2">{{ stat.value }}</span>
      </div>
    </div>

    <!-- Campaigns List Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-10 h-10 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>
      <div v-else>
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-slate-800 bg-slate-900/50">
              <th class="px-6 py-4.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Рассылка</th>
              <th class="px-6 py-4.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Целевой сегмент</th>
              <th class="px-6 py-4.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Дата отправки</th>
              <th class="px-6 py-4.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Статус</th>
              <th class="px-6 py-4.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">Прогресс отправки</th>
              <th class="px-6 py-4.5 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800 bg-slate-900/20">
            <tr v-for="m in mailings" :key="m.id" class="hover:bg-slate-800/30 transition-colors">
              <!-- Mailing title & sample message -->
              <td class="px-6 py-4.5">
                <p class="font-bold text-white text-[15px]">{{ m.title }}</p>
                <p class="text-slate-500 text-xs truncate max-w-xs mt-1">{{ m.message_ru }}</p>
              </td>

              <!-- Audience Segment -->
              <td class="px-6 py-4.5">
                <span class="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full border"
                  :class="segmentClass(m.audience_type)">
                  {{ segmentLabel(m.audience_type) }}
                </span>
              </td>

              <!-- Scheduled Date -->
              <td class="px-6 py-4.5 text-sm text-slate-300">
                {{ formatDateTime(m.scheduled_at) }}
              </td>

              <!-- Status -->
              <td class="px-6 py-4.5">
                <span class="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border"
                  :class="statusClass(m.status)">
                  <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass(m.status)"></span>
                  {{ statusLabel(m.status) }}
                </span>
              </td>

              <!-- Progress bar & metrics -->
              <td class="px-6 py-4.5 min-w-[200px]">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
                  <span>{{ progressPercent(m) }}%</span>
                  <span>{{ m.sent_success + m.failed_count + m.unsubscribed_count }} / {{ m.total_recipients || '?' }}</span>
                </div>
                <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div class="bg-indigo-500 h-1.5 rounded-full transition-all duration-500"
                       :style="{ width: `${progressPercent(m)}%` }"></div>
                </div>
                <div class="flex gap-2 text-[10px] text-slate-500 mt-1">
                  <span class="text-emerald-400">✓ {{ m.sent_success }}</span>
                  <span class="text-rose-400">✗ {{ m.failed_count }}</span>
                  <span class="text-amber-400">🚪 {{ m.unsubscribed_count }}</span>
                </div>
              </td>

              <!-- Action buttons -->
              <td class="px-6 py-4.5 text-right space-x-2">
                <button
                  @click="openTestModal(m)"
                  title="Тестовая отправка"
                  class="border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 p-2 rounded-xl transition-all inline-flex items-center"
                >
                  🧪 Тест
                </button>
                <button
                  v-if="canDelete(m)"
                  @click="deleteMailing(m.id)"
                  title="Удалить"
                  class="border border-rose-950/40 text-rose-400 hover:text-white hover:bg-rose-900/30 p-2 rounded-xl transition-all inline-flex items-center"
                >
                  🗑️
                </button>
              </td>
            </tr>
            <tr v-if="!mailings.length">
              <td colspan="6" class="px-6 py-16 text-center text-slate-500 font-medium">
                Рассылки отсутствуют. Нажмите «Создать рассылку», чтобы запустить новую кампанию.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="createModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <!-- Modal header -->
        <div class="px-8 py-5 border-b border-slate-800 flex items-center justify-between">
          <h2 class="text-xl font-bold text-white">Новая рассылка</h2>
          <button @click="closeCreateModal" class="text-slate-400 hover:text-white text-lg bg-transparent border-none cursor-pointer">✕</button>
        </div>

        <!-- Modal body -->
        <div class="px-8 py-6 max-h-[70vh] overflow-y-auto space-y-6">
          <!-- Title -->
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-slate-300">Название кампании</label>
            <input
              v-model="newMailing.title"
              type="text"
              placeholder="Например: Скидки в будние дни"
              class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-600 transition-all"
            />
          </div>

          <!-- Target Segment & Count -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="block text-sm font-semibold text-slate-300">Сегмент получателей</label>
              <select
                v-model="newMailing.audience_type"
                @change="fetchAudienceCount"
                class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              >
                <option value="all">Все клиенты</option>
                <option value="active">Активные (визит за 60 дней)</option>
                <option value="inactive">Неактивные (> 60 дней)</option>
              </select>
            </div>

            <!-- Scheduled time -->
            <div class="space-y-2">
              <label class="block text-sm font-semibold text-slate-300">Время отправки</label>
              <input
                v-model="newMailing.scheduled_at"
                type="datetime-local"
                class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          <!-- Audience size badge -->
          <div v-if="audienceCountLoading" class="text-xs text-indigo-400 animate-pulse">
            ⏳ Подсчет размера аудитории...
          </div>
          <div v-else-if="audienceCount !== null" class="bg-indigo-950/40 border border-indigo-900/60 text-indigo-300 px-4 py-3 rounded-xl text-xs flex items-center justify-between">
            <span>Размер целевой аудитории:</span>
            <span class="font-extrabold text-sm text-indigo-200">{{ audienceCount }} человек(а)</span>
          </div>

          <!-- Template tabs / inputs -->
          <div class="space-y-4">
            <div class="flex border-b border-slate-800">
              <button
                @click="activeLangTab = 'ru'"
                class="px-4 py-2 border-b-2 text-sm font-semibold transition-all bg-transparent cursor-pointer"
                :class="activeLangTab === 'ru' ? 'border-indigo-500 text-white' : 'border-transparent text-slate-500 hover:text-slate-300'"
              >
                На русском (RU)
              </button>
              <button
                @click="activeLangTab = 'kz'"
                class="px-4 py-2 border-b-2 text-sm font-semibold transition-all bg-transparent cursor-pointer"
                :class="activeLangTab === 'kz' ? 'border-indigo-500 text-white' : 'border-transparent text-slate-500 hover:text-slate-300'"
              >
                На казахском (KZ)
              </button>
            </div>

            <div class="space-y-2">
              <div class="flex justify-between items-center">
                <label class="block text-xs font-semibold text-slate-400">Текст сообщения</label>
                <button
                  @click="insertPlaceholder"
                  class="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 transition-colors bg-indigo-950/50 hover:bg-indigo-900/50 border border-indigo-800/40 px-2.5 py-1 rounded-lg cursor-pointer"
                >
                  👤 Вставить имя {{user_name}}
                </button>
              </div>

              <!-- Message Textarea (RU) -->
              <textarea
                v-if="activeLangTab === 'ru'"
                ref="textarea_ru"
                v-model="newMailing.message_ru"
                rows="5"
                placeholder="Привет, {{user_name}}! Дарим вам..."
                class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-700 transition-all font-sans leading-relaxed"
              ></textarea>

              <!-- Message Textarea (KZ) -->
              <textarea
                v-if="activeLangTab === 'kz'"
                ref="textarea_kz"
                v-model="newMailing.message_kz"
                rows="5"
                placeholder="Сәлем, {{user_name}}! Тек сіз үшін..."
                class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-700 transition-all font-sans leading-relaxed"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Modal footer -->
        <div class="px-8 py-5 border-t border-slate-800 flex justify-end gap-3 bg-slate-950/30">
          <button
            @click="closeCreateModal"
            class="px-5 py-2.5 border border-slate-800 text-slate-400 hover:text-white rounded-xl text-sm font-semibold transition-all bg-transparent cursor-pointer"
          >
            Отмена
          </button>
          <button
            type="button"
            @click="openTestModal(newMailing)"
            :disabled="!newMailing.message_ru.trim() && !newMailing.message_kz.trim()"
            class="px-5 py-2.5 border border-indigo-500/30 text-indigo-400 hover:text-white hover:bg-indigo-650/20 rounded-xl text-sm font-semibold transition-all active:scale-95 disabled:opacity-50 cursor-pointer flex items-center gap-2"
          >
            🧪 Тест
          </button>
          <button
            @click="createMailing"
            :disabled="saving"
            class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg hover:shadow-indigo-500/10 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            {{ saving ? 'Сохранение...' : 'Запланировать' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Test Delivery Modal -->
    <div v-if="testModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-md overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <!-- Modal header -->
        <div class="px-6 py-5 border-b border-slate-800 flex items-center justify-between">
          <h2 class="text-lg font-bold text-white">Тестовая отправка</h2>
          <button @click="closeTestModal" class="text-slate-400 hover:text-white text-lg bg-transparent border-none cursor-pointer">✕</button>
        </div>

        <!-- Modal body -->
        <div class="px-6 py-6 space-y-4">
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-slate-300">Ваш Telegram ID</label>
            <input
              v-model="testTelegramId"
              type="text"
              placeholder="Введите ваш Telegram ID"
              class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder:text-slate-600 transition-all"
            />
          </div>

          <div class="text-xs text-slate-400 bg-slate-950 border border-slate-850 p-4.5 rounded-xl leading-relaxed">
            💡 Узнать свой ID можно, написав команду <code class="text-indigo-400 bg-indigo-950/40 px-1.5 py-0.5 rounded font-mono font-bold">/getmyid</code> боту заведения в Telegram.
          </div>
        </div>

        <!-- Modal footer -->
        <div class="px-6 py-4 border-t border-slate-800 flex justify-end gap-2 bg-slate-950/30">
          <button
            @click="closeTestModal"
            class="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-xl text-sm font-semibold transition-all bg-transparent cursor-pointer"
          >
            Закрыть
          </button>
          <button
            @click="sendTestMailing"
            :disabled="sendingTest"
            class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg hover:shadow-indigo-500/10 transition-all active:scale-95 disabled:opacity-50 cursor-pointer flex items-center gap-2"
          >
            <span v-if="sendingTest" class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
            {{ sendingTest ? 'Отправка...' : 'Отправить тест' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const mailings = ref([])
const loading = ref(true)

// Create modal state
const createModalOpen = ref(false)
const saving = ref(false)
const newMailing = ref({
  title: '',
  audience_type: 'all',
  scheduled_at: '',
  message_ru: '',
  message_kz: '',
})
const activeLangTab = ref('ru')
const audienceCount = ref(null)
const audienceCountLoading = ref(false)

// Input textareas references
const textarea_ru = ref(null)
const textarea_kz = ref(null)

// Test modal state
const testModalOpen = ref(false)
const sendingTest = ref(false)
const testTelegramId = ref('')
const activeTestMailing = ref(null)

// Computed overall analytics
const generalStats = computed(() => {
  const total = mailings.value.length
  const scheduled = mailings.value.filter(m => m.status === 'scheduled').length
  const active = mailings.value.filter(m => m.status === 'in_progress').length
  const completed = mailings.value.filter(m => m.status === 'done').length
  return [
    { label: 'Всего рассылок', value: total },
    { label: 'Запланировано', value: scheduled },
    { label: 'В процессе', value: active },
    { label: 'Завершено', value: completed },
  ]
})

// Load existing mailings
async function loadMailings() {
  try {
    const res = await api.get('/mailings/', {
      params: { organization_id: auth.currentOrgId }
    })
    mailings.value = res.data
  } catch (e) {
    toast.error('Не удалось загрузить список рассылок')
  } finally {
    loading.value = false
  }
}

// Check if task can be deleted
function canDelete(m) {
  return m.status === 'draft' || m.status === 'scheduled'
}

// Delete campaign
async function deleteMailing(id) {
  if (!confirm('Вы действительно хотите удалить эту рассылку?')) return
  try {
    await api.delete(`/mailings/${id}/`)
    toast.success('Рассылка успешно удалена')
    loadMailings()
  } catch (e) {
    toast.error(e.response?.data?.error || 'Не удалось удалить рассылку')
  }
}

// Fetch audience count dynamically
async function fetchAudienceCount() {
  audienceCountLoading.value = true
  try {
    const res = await api.get('/mailings/count_recipients/', {
      params: {
        audience_type: newMailing.value.audience_type,
        organization_id: auth.currentOrgId
      }
    })
    audienceCount.value = res.data.count
  } catch (e) {
    audienceCount.value = null
  } finally {
    audienceCountLoading.value = false
  }
}

// Insert cursor helper placeholder
function insertPlaceholder() {
  const isRu = activeLangTab.value === 'ru'
  const textarea = isRu ? textarea_ru.value : textarea_kz.value
  if (!textarea) return

  const text = isRu ? newMailing.value.message_ru : newMailing.value.message_kz
  const start = textarea.selectionStart
  const end = textarea.selectionEnd

  const updatedText = text.substring(0, start) + '{{user_name}}' + text.substring(end)
  if (isRu) {
    newMailing.value.message_ru = updatedText
  } else {
    newMailing.value.message_kz = updatedText
  }

  nextTick(() => {
    textarea.focus()
    const offset = start + '{{user_name}}'.length
    textarea.setSelectionRange(offset, offset)
  })
}

// Create campaign
async function createMailing() {
  if (!newMailing.value.title.trim()) return toast.error('Укажите название рассылки')
  if (!newMailing.value.scheduled_at) return toast.error('Укажите время отправки')
  if (!newMailing.value.message_ru.trim()) return toast.error('Заполните шаблон сообщения на русском')
  if (!newMailing.value.message_kz.trim()) return toast.error('Заполните шаблон сообщения на казахском')

  saving.value = true
  try {
    await api.post('/mailings/', {
      ...newMailing.value,
      organization_id: auth.currentOrgId
    })
    toast.success('Рассылка успешно запланирована')
    closeCreateModal()
    loadMailings()
  } catch (e) {
    toast.error('Не удалось запланировать рассылку')
  } finally {
    saving.value = false
  }
}

// Test modal trigger
function openTestModal(mailing) {
  activeTestMailing.value = mailing
  testTelegramId.value = auth.user?.telegram_id || ''
  testModalOpen.value = true
}

function closeTestModal() {
  testModalOpen.value = false
  activeTestMailing.value = null
}

async function sendTestMailing() {
  if (!testTelegramId.value.trim()) return toast.error('Укажите Telegram ID')
  sendingTest.value = true
  try {
    if (activeTestMailing.value && activeTestMailing.value.id) {
      await api.post(`/mailings/${activeTestMailing.value.id}/send_test/`, {
        telegram_id: testTelegramId.value.trim()
      })
    } else {
      // Testing unsaved mailing preview
      await api.post(`/mailings/send_test_preview/`, {
        telegram_id: testTelegramId.value.trim(),
        message_ru: activeTestMailing.value.message_ru,
        message_kz: activeTestMailing.value.message_kz
      })
    }
    toast.success('Тестовое сообщение успешно отправлено')
    if (auth.user) {
      auth.user.telegram_id = testTelegramId.value.trim()
    }
    closeTestModal()
  } catch (e) {
    toast.error('Не удалось отправить тестовое сообщение')
  } finally {
    sendingTest.value = false
  }
}

// Dialog management
function openCreateModal() {
  // Set default datetime to now + 10 mins formatted as YYYY-MM-DDTHH:mm
  const date = new Date(Date.now() + 10 * 60 * 1000)
  const offset = date.getTimezoneOffset() * 60 * 1000
  const localDate = new Date(date.getTime() - offset)
  const defaultDateTime = localDate.toISOString().slice(0, 16)

  newMailing.value = {
    title: '',
    audience_type: 'all',
    scheduled_at: defaultDateTime,
    message_ru: '',
    message_kz: '',
  }
  activeLangTab.value = 'ru'
  audienceCount.value = null
  createModalOpen.value = true
  fetchAudienceCount()
}

function closeCreateModal() {
  createModalOpen.value = false
}

// Helpers
function formatDateTime(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('ru-RU', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function progressPercent(m) {
  if (!m.total_recipients) return 0
  const processed = m.sent_success + m.failed_count + m.unsubscribed_count
  return Math.min(100, Math.round((processed / m.total_recipients) * 100))
}

function segmentLabel(segment) {
  const labels = {
    all: 'Все',
    active: 'Активные',
    inactive: 'Неактивные',
  }
  return labels[segment] || segment
}

function segmentClass(segment) {
  const styles = {
    all: 'border-slate-800 bg-slate-950 text-slate-300',
    active: 'border-emerald-950 text-emerald-400 bg-emerald-950/20',
    inactive: 'border-amber-950 text-amber-500 bg-amber-950/20',
  }
  return styles[segment] || styles.all
}

function statusLabel(status) {
  const labels = {
    draft: 'Черновик',
    scheduled: 'Запланирована',
    in_progress: 'В процессе',
    done: 'Завершена',
    error: 'Ошибка',
  }
  return labels[status] || status
}

function statusClass(status) {
  const styles = {
    draft: 'border-slate-800 text-slate-400 bg-slate-950',
    scheduled: 'border-indigo-950 text-indigo-400 bg-indigo-950/20',
    in_progress: 'border-sky-950 text-sky-400 bg-sky-950/20',
    done: 'border-emerald-950 text-emerald-400 bg-emerald-950/20',
    error: 'border-rose-950 text-rose-400 bg-rose-950/20',
  }
  return styles[status] || styles.draft
}

function statusDotClass(status) {
  const styles = {
    draft: 'bg-slate-400',
    scheduled: 'bg-indigo-400',
    in_progress: 'bg-sky-400',
    done: 'bg-emerald-400',
    error: 'bg-rose-400',
  }
  return styles[status] || styles.draft
}

onMounted(loadMailings)
</script>

<style scoped>
/* Basic fade transitions for modern look */
.animate-in {
  animation: modal-enter 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes modal-enter {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
