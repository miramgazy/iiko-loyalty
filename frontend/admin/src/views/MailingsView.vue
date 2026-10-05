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
                <div class="flex items-center gap-2">
                  <p class="font-bold text-white text-[15px]">{{ m.title }}</p>
                  <span v-if="m.has_image" class="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-md bg-indigo-950/80 text-indigo-300 border border-indigo-800/60" title="Рассылка с фото">
                    📷 С фото
                  </span>
                </div>
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

          <!-- Photo broadcast toggle & upload section -->
          <div class="p-4 bg-slate-950/70 border border-slate-800 rounded-2xl space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-lg">
                  📷
                </div>
                <div>
                  <label for="toggle-has-image" class="text-sm font-bold text-white cursor-pointer select-none">
                    Отправить текст с фото
                  </label>
                  <p class="text-xs text-slate-400 mt-0.5">
                    Прикрепить рекламное изображение к рассылке
                  </p>
                </div>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  id="toggle-has-image"
                  type="checkbox"
                  v-model="newMailing.has_image"
                  @change="onToggleHasImage"
                  class="sr-only peer"
                />
                <div class="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            <!-- Expanded Section when has_image is ON -->
            <div v-if="newMailing.has_image" class="pt-3 border-t border-slate-800 space-y-4 animate-in">
              <!-- Hidden File Input -->
              <input
                ref="fileInputRef"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                class="hidden"
                @change="handleFileSelect"
              />

              <!-- Dropzone when no image selected -->
              <div
                v-if="!selectedImageFile"
                @click="triggerFileInput"
                @dragover.prevent
                @drop.prevent="handleFileDrop"
                class="border-2 border-dashed border-slate-800 hover:border-indigo-500/50 bg-slate-950/40 hover:bg-slate-900/50 rounded-2xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2 group"
              >
                <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 group-hover:bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-2xl transition-all">
                  📤
                </div>
                <div>
                  <span class="text-sm font-semibold text-indigo-400 hover:underline">Выберите фото</span>
                  <span class="text-sm text-slate-400"> или перетащите файл сюда</span>
                </div>
                <p class="text-xs text-slate-500">Поддерживаются форматы JPG, PNG, WEBP (до 5 МБ)</p>
              </div>

              <!-- Image Preview Card -->
              <div v-else class="flex items-center justify-between p-3.5 bg-slate-900 border border-slate-800 rounded-2xl">
                <div class="flex items-center gap-3.5 overflow-hidden">
                  <img :src="imagePreviewUrl" alt="Превью" class="w-14 h-14 rounded-xl object-cover border border-slate-700/50 flex-shrink-0" />
                  <div class="min-w-0">
                    <p class="text-sm font-semibold text-white truncate">{{ selectedImageFile.name }}</p>
                    <p class="text-xs text-slate-400 mt-0.5">{{ formatFileSize(selectedImageFile.size) }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <button
                    type="button"
                    @click="triggerFileInput"
                    class="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 transition-all cursor-pointer"
                  >
                    Заменить
                  </button>
                  <button
                    type="button"
                    @click="removeSelectedImage"
                    class="text-xs font-semibold px-3 py-1.5 rounded-xl border border-rose-950/40 text-rose-400 hover:text-white hover:bg-rose-900/30 transition-all cursor-pointer"
                  >
                    ✕ Удалить
                  </button>
                </div>
              </div>

              <!-- Telegram Test ID & Get File ID -->
              <div class="p-4 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-3">
                <div class="flex flex-col sm:flex-row sm:items-end gap-3">
                  <div class="flex-1 space-y-1.5">
                    <label class="block text-xs font-semibold text-slate-300">
                      Telegram ID для тестовой отправки
                    </label>
                    <input
                      v-model="newMailing.tg_id_for_test"
                      type="text"
                      placeholder="Например: 123456789"
                      class="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all placeholder:text-slate-600"
                    />
                  </div>
                  <button
                    type="button"
                    @click="fetchFileId"
                    :disabled="gettingFileId || !selectedImageFile || !newMailing.tg_id_for_test?.trim()"
                    class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl text-sm transition-all shadow-md active:scale-95 flex items-center justify-center gap-2 cursor-pointer flex-shrink-0"
                  >
                    <span v-if="gettingFileId" class="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
                    <span>{{ gettingFileId ? 'Отправка...' : '⚡ Получить File ID' }}</span>
                  </button>
                </div>

                <!-- Status of File ID -->
                <div v-if="newMailing.telegram_file_id" class="flex items-center justify-between p-3 rounded-xl bg-emerald-950/30 border border-emerald-900/50 text-xs text-emerald-300">
                  <div class="flex items-center gap-2 overflow-hidden">
                    <span class="text-emerald-400 text-base">✓</span>
                    <div class="truncate">
                      <span class="font-bold">File ID получен:</span>
                      <span class="font-mono text-emerald-200 ml-1.5">{{ newMailing.telegram_file_id }}</span>
                    </div>
                  </div>
                  <span class="text-[11px] font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40 ml-2 whitespace-nowrap">
                    Готово к отправке
                  </span>
                </div>
                <div v-else class="flex items-center gap-2 p-3 rounded-xl bg-amber-950/30 border border-amber-900/50 text-xs text-amber-300">
                  <span class="text-amber-400">⚠️</span>
                  <span>Для подтверждения фото нажмите «Получить File ID». На ваш Telegram придёт тестовое фото с текстом.</span>
                </div>
              </div>
            </div>
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

              <!-- Character counter & caption limit notice -->
              <div class="flex justify-between items-center text-xs mt-1.5 px-1">
                <span class="text-slate-500">
                  {{ newMailing.has_image ? 'Лимит подписи к фото: 1024 символа' : 'Лимит сообщения: 4096 символов' }}
                </span>
                <span
                  :class="currentCaptionLength > maxAllowedCaptionLength ? 'text-rose-400 font-bold' : 'text-slate-400'"
                >
                  {{ currentCaptionLength }} / {{ maxAllowedCaptionLength }}
                </span>
              </div>
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

// Photo broadcast state
const selectedImageFile = ref(null)
const imagePreviewUrl = ref('')
const fileInputRef = ref(null)
const gettingFileId = ref(false)

const newMailing = ref({
  title: '',
  audience_type: 'all',
  scheduled_at: '',
  message_ru: '',
  message_kz: '',
  has_image: false,
  tg_id_for_test: '',
  telegram_file_id: '',
})
const activeLangTab = ref('ru')
const audienceCount = ref(null)
const audienceCountLoading = ref(false)

// Caption limits
const maxAllowedCaptionLength = computed(() => (newMailing.value.has_image ? 1024 : 4096))
const currentCaptionLength = computed(() => {
  return activeLangTab.value === 'ru'
    ? (newMailing.value.message_ru || '').length
    : (newMailing.value.message_kz || '').length
})

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

// Photo file handling methods
function onToggleHasImage() {
  if (!newMailing.value.has_image) {
    removeSelectedImage()
  } else {
    if (!newMailing.value.tg_id_for_test && auth.user?.telegram_id) {
      newMailing.value.tg_id_for_test = String(auth.user.telegram_id)
    }
  }
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (!file) return
  processSelectedFile(file)
}

function handleFileDrop(e) {
  const file = e.dataTransfer?.files?.[0]
  if (!file) return
  processSelectedFile(file)
}

function processSelectedFile(file) {
  const validTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!validTypes.includes(file.type)) {
    return toast.error('Поддерживаются только изображения JPG, PNG или WEBP')
  }
  if (file.size > 5 * 1024 * 1024) {
    return toast.error('Размер файла не должен превышать 5 МБ')
  }
  selectedImageFile.value = file
  imagePreviewUrl.value = URL.createObjectURL(file)
  newMailing.value.telegram_file_id = ''
}

function removeSelectedImage() {
  selectedImageFile.value = null
  imagePreviewUrl.value = ''
  newMailing.value.telegram_file_id = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
}

async function fetchFileId() {
  if (!selectedImageFile.value) {
    return toast.error('Сначала выберите изображение')
  }
  const tgId = newMailing.value.tg_id_for_test?.trim()
  if (!tgId) {
    return toast.error('Укажите Telegram ID для тестовой отправки')
  }

  gettingFileId.value = true
  try {
    const fd = new FormData()
    fd.append('image', selectedImageFile.value)
    fd.append('tg_id_for_test', tgId)
    fd.append('message_ru', newMailing.value.message_ru || 'Тестовая рассылка с изображением')
    fd.append('message_kz', newMailing.value.message_kz || 'Суретпен тесттік хабарлама')
    fd.append('organization_id', auth.currentOrgId)

    const res = await api.post('/mailings/get_file_id/', fd)
    newMailing.value.telegram_file_id = res.data.file_id
    if (auth.user) {
      auth.user.telegram_id = tgId
    }
    toast.success('Тестовое фото отправлено! File ID успешно получен.')
  } catch (e) {
    const msg = e.response?.data?.error || e.response?.data?.detail || 'Не удалось получить File ID через Telegram'
    toast.error(msg)
  } finally {
    gettingFileId.value = false
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

  if (newMailing.value.has_image) {
    if (!selectedImageFile.value) {
      return toast.error('Загрузите изображение для отправки с фото')
    }
    if (!newMailing.value.telegram_file_id) {
      return toast.error('Для отправки с фото сначала получите File ID, нажав кнопку «Получить File ID»')
    }
    if (newMailing.value.message_ru.length > 1024) {
      return toast.error('Подпись к фото на русском не должна превышать 1024 символа')
    }
    if (newMailing.value.message_kz.length > 1024) {
      return toast.error('Подпись к фото на казахском не должна превышать 1024 символа')
    }
  }

  saving.value = true
  try {
    const formData = new FormData()
    formData.append('title', newMailing.value.title.trim())
    formData.append('audience_type', newMailing.value.audience_type)
    formData.append('scheduled_at', newMailing.value.scheduled_at)
    formData.append('message_ru', newMailing.value.message_ru)
    formData.append('message_kz', newMailing.value.message_kz)
    formData.append('organization_id', auth.currentOrgId)
    formData.append('has_image', newMailing.value.has_image ? 'true' : 'false')

    if (newMailing.value.has_image) {
      if (selectedImageFile.value) {
        formData.append('image', selectedImageFile.value)
      }
      if (newMailing.value.tg_id_for_test) {
        formData.append('tg_id_for_test', newMailing.value.tg_id_for_test.trim())
      }
      if (newMailing.value.telegram_file_id) {
        formData.append('telegram_file_id', newMailing.value.telegram_file_id)
      }
    }

    await api.post('/mailings/', formData)
    toast.success('Рассылка успешно запланирована')
    closeCreateModal()
    loadMailings()
  } catch (e) {
    const errorMsg = e.response?.data?.message_ru?.[0] || e.response?.data?.error || 'Не удалось запланировать рассылку'
    toast.error(errorMsg)
  } finally {
    saving.value = false
  }
}

// Test modal trigger
function openTestModal(mailing) {
  activeTestMailing.value = mailing
  testTelegramId.value = mailing?.tg_id_for_test || auth.user?.telegram_id || ''
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
      const fd = new FormData()
      fd.append('telegram_id', testTelegramId.value.trim())
      fd.append('message_ru', activeTestMailing.value.message_ru || '')
      fd.append('message_kz', activeTestMailing.value.message_kz || '')
      fd.append('organization_id', auth.currentOrgId)
      if (activeTestMailing.value?.has_image) {
        fd.append('has_image', 'true')
        if (activeTestMailing.value?.telegram_file_id) {
          fd.append('telegram_file_id', activeTestMailing.value.telegram_file_id)
        } else if (selectedImageFile.value) {
          fd.append('image', selectedImageFile.value)
        }
      }
      await api.post(`/mailings/send_test_preview/`, fd)
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
    has_image: false,
    tg_id_for_test: auth.user?.telegram_id ? String(auth.user.telegram_id) : '',
    telegram_file_id: '',
  }
  selectedImageFile.value = null
  imagePreviewUrl.value = ''
  if (fileInputRef.value) fileInputRef.value.value = ''
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
