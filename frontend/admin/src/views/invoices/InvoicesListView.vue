<template>
  <div class="p-8 space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-2">
          <span>🧾</span> Приходные накладные (AI Invoices)
        </h1>
        <p class="text-slate-400 text-sm mt-1">Распознавание накладных с Vision LLM, сопоставление номенклатуры и импорт в iiko</p>
      </div>

      <div class="flex items-center gap-3">
        <RouterLink to="/admin/invoices/knowledge-base"
          class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-sm font-medium transition-colors flex items-center gap-2">
          <span>🧠</span> База знаний
        </RouterLink>
        <button @click="showUploadModal = true"
          class="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2">
          <span>+</span> Загрузить накладную
        </button>
      </div>
    </div>

    <!-- Drag & Drop Quick Dropzone Banner -->
    <div
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleFileDrop"
      class="border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer"
      :class="isDragging ? 'border-indigo-500 bg-indigo-950/20 scale-[0.99]' : 'border-slate-800 bg-slate-900/60 hover:border-slate-700'"
      @click="showUploadModal = true"
    >
      <div class="max-w-md mx-auto flex flex-col items-center">
        <div class="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-2xl mb-3">
          📥
        </div>
        <h3 class="text-white font-semibold text-sm">Перетащите сканы, фото или PDF накладных сюда</h3>
        <p class="text-slate-400 text-xs mt-1">Поддерживаются форматы JPG, PNG, WEBP и многостраничные PDF. Распознавание печатных и рукописных накладных.</p>
      </div>
    </div>

    <!-- Filters Block -->
    <div class="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
      <!-- Top row: Status pills & Reset button -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <!-- Status Pills -->
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full">
          <button
            v-for="st in filterStatuses"
            :key="st.value"
            @click="selectedStatus = st.value; loadInvoices()"
            class="px-3 py-1.5 rounded-xl text-xs font-semibold transition-all whitespace-nowrap cursor-pointer"
            :class="selectedStatus === st.value
              ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
              : 'bg-slate-950/60 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800'"
          >
            {{ st.label }}
          </button>
        </div>

        <!-- Reset Button & Active Count -->
        <div v-if="hasActiveFilters" class="flex items-center gap-2 self-end lg:self-auto flex-shrink-0">
          <span class="text-[11px] px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
            Активно фильтров: {{ activeFiltersCount }}
          </span>
          <button
            type="button"
            @click="resetAllFilters"
            class="text-xs text-rose-400 hover:text-rose-300 font-semibold hover:underline flex items-center gap-1 cursor-pointer transition-colors"
          >
            <span>✕</span>
            <span>Сбросить всё</span>
          </button>
        </div>
      </div>

      <!-- Main Filter Controls Grid -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-3.5 pt-3 border-t border-slate-800/80">
        <!-- 1. Supplier / Counterparty Combobox (5 cols) -->
        <div class="md:col-span-5 relative" ref="supplierDropdownRef">
          <label class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
            <span class="flex items-center gap-1.5">
              <span>🏢</span> Контрагент (поставщик)
            </span>
            <span v-if="selectedSupplier" class="text-[10px] text-indigo-400 font-mono">Выбран из списка</span>
          </label>
          <div class="relative">
            <input
              v-model="supplierSearchText"
              @focus="isSupplierDropdownOpen = true"
              @input="handleSupplierInput"
              type="text"
              placeholder="Начните вводить название поставщика..."
              class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none transition-colors pr-8"
            />
            <button
              v-if="supplierSearchText"
              type="button"
              @click="clearSupplier"
              class="absolute right-2.5 top-2 text-slate-500 hover:text-slate-300 text-xs cursor-pointer p-0.5"
              title="Очистить"
            >
              ✕
            </button>
            <span v-else class="absolute right-3 top-2.5 text-slate-500 text-[10px] pointer-events-none">▼</span>
          </div>

          <!-- Dropdown List with matching suppliers -->
          <Transition name="fade">
            <div
              v-if="isSupplierDropdownOpen"
              class="absolute left-0 right-0 top-full mt-1.5 max-h-60 overflow-y-auto bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl z-30 divide-y divide-slate-800/80"
            >
              <div
                v-if="filteredSuppliers.length === 0"
                class="p-3 text-center text-xs text-slate-500"
              >
                Поставщик не найден
              </div>
              <div v-else>
                <div
                  @click="clearSupplier"
                  class="px-3.5 py-2 text-xs text-indigo-300 hover:bg-slate-800 cursor-pointer flex items-center justify-between transition-colors"
                >
                  <span class="font-semibold">Все поставщики</span>
                  <span v-if="!selectedSupplier && !supplierSearchText" class="text-indigo-400 font-bold">✓</span>
                </div>
                <div
                  v-for="sup in filteredSuppliers"
                  :key="sup.id || sup.name"
                  @click="selectSupplier(sup)"
                  class="px-3.5 py-2 text-xs text-slate-200 hover:bg-slate-800 hover:text-white cursor-pointer flex items-center justify-between transition-colors"
                  :class="selectedSupplier?.name === sup.name ? 'bg-indigo-950/40 text-indigo-200 font-bold' : ''"
                >
                  <div class="truncate pr-2">
                    <p class="truncate">{{ sup.name }}</p>
                    <p v-if="sup.inn" class="text-[10px] text-slate-500 font-mono">ИНН: {{ sup.inn }}</p>
                  </div>
                  <span v-if="selectedSupplier?.name === sup.name" class="text-indigo-400 font-bold">✓</span>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- 2. Invoice Number Input (3 cols) -->
        <div class="md:col-span-3">
          <label class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
            <span>🧾</span> Номер накладной
          </label>
          <div class="relative">
            <input
              v-model="invoiceNumberQuery"
              @input="handleNumberInput"
              type="text"
              placeholder="Номер документа..."
              class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none transition-colors pr-8"
            />
            <button
              v-if="invoiceNumberQuery"
              type="button"
              @click="clearNumber"
              class="absolute right-2.5 top-2 text-slate-500 hover:text-slate-300 text-xs cursor-pointer p-0.5"
              title="Очистить"
            >
              ✕
            </button>
            <span v-else class="absolute right-3 top-2.5 text-slate-500 text-xs pointer-events-none">🔍</span>
          </div>
        </div>

        <!-- 3. Date Range (4 cols) -->
        <div class="md:col-span-4">
          <div class="flex items-center justify-between mb-1.5">
            <label class="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>📅</span> Период
            </label>
            <!-- Presets links -->
            <div class="flex items-center gap-1.5 text-[10px]">
              <button
                type="button"
                @click="setDatePreset('today')"
                class="text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
                :class="activeDatePreset === 'today' ? 'text-indigo-400 font-bold underline' : ''"
              >
                Сегодня
              </button>
              <span class="text-slate-700">•</span>
              <button
                type="button"
                @click="setDatePreset('week')"
                class="text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
                :class="activeDatePreset === 'week' ? 'text-indigo-400 font-bold underline' : ''"
              >
                7 дней
              </button>
              <span class="text-slate-700">•</span>
              <button
                type="button"
                @click="setDatePreset('month')"
                class="text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
                :class="activeDatePreset === 'month' ? 'text-indigo-400 font-bold underline' : ''"
              >
                30 дней
              </button>
              <span class="text-slate-700">•</span>
              <button
                type="button"
                @click="setDatePreset('this_month')"
                class="text-slate-400 hover:text-indigo-400 transition-colors cursor-pointer"
                :class="activeDatePreset === 'this_month' ? 'text-indigo-400 font-bold underline' : ''"
              >
                Месяц
              </button>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div class="relative">
              <input
                v-model="dateFrom"
                @change="handleDateChange"
                type="date"
                class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none transition-colors [color-scheme:dark]"
                title="Дата с"
              />
            </div>
            <div class="relative">
              <input
                v-model="dateTo"
                @change="handleDateChange"
                type="date"
                class="w-full bg-slate-950 border border-slate-800 focus:border-indigo-500 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none transition-colors [color-scheme:dark]"
                title="Дата по"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Invoices Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-max text-left text-sm text-slate-300">
          <thead>
            <tr class="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider bg-slate-950/40 whitespace-nowrap">
              <th class="px-6 py-4">Документ</th>
              <th class="px-6 py-4">Поставщик</th>
              <th class="px-6 py-4">Склад iiko</th>
              <th class="px-6 py-4">Сумма</th>
              <th class="px-6 py-4">Статус</th>
              <th class="px-6 py-4">Источник</th>
              <th class="px-6 py-4">Автор</th>
              <th class="px-6 py-4 text-right">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800 whitespace-nowrap">
            <tr v-for="inv in invoices" :key="inv.id" class="hover:bg-slate-850/50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-sm font-mono text-indigo-300 flex-shrink-0">
                    📄
                  </div>
                  <div>
                    <div class="font-bold text-white flex items-center gap-2">
                      {{ inv.invoice_number || inv.internal_number }}
                      <span v-if="inv.images_count > 1" class="text-[10px] px-1.5 py-0.2 bg-slate-800 text-slate-400 rounded">
                        {{ inv.images_count }} стр.
                      </span>
                    </div>
                    <p class="text-[11px] text-slate-500">{{ inv.invoice_date || formatDate(inv.created_at) }}</p>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <p class="font-medium text-white">{{ inv.iiko_supplier_name || inv.raw_supplier_name || '—' }}</p>
                <p v-if="inv.raw_supplier_inn" class="text-[11px] text-slate-500 font-mono">ИНН: {{ inv.raw_supplier_inn }}</p>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="text-xs text-slate-300">{{ inv.iiko_store_name || 'Не выбран' }}</span>
              </td>
              <td class="px-6 py-4 font-mono font-bold text-white whitespace-nowrap">
                {{ inv.total_sum ? Number(inv.total_sum).toLocaleString('ru-RU', { minimumFractionDigits: 2 }) + ' ₸' : '—' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border whitespace-nowrap"
                  :class="statusBadgeClass(inv.status)">
                  <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass(inv.status)"></span>
                  {{ inv.status_display }}
                </span>
              </td>
              <td class="px-6 py-4 text-xs text-slate-400 whitespace-nowrap">
                <span class="px-2 py-0.5 rounded bg-slate-800 font-mono text-[11px] whitespace-nowrap">
                  {{ inv.source === 'tma' ? '📱 TMA' : '💻 Админка' }}
                </span>
              </td>
              <td class="px-6 py-4 text-xs whitespace-nowrap">
                <div v-if="inv.author?.name" class="flex flex-col whitespace-nowrap">
                  <span class="font-medium text-white">{{ inv.author.name }}</span>
                  <span v-if="inv.author.role" class="text-[11px] text-slate-400">{{ inv.author.role }}</span>
                </div>
                <span v-else class="text-slate-500">—</span>
              </td>
              <td class="px-6 py-4 text-right whitespace-nowrap">
                <div class="flex items-center justify-end gap-2 whitespace-nowrap">
                  <RouterLink :to="`/admin/invoices/${inv.id}`"
                    class="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5">
                    <span>Открыть</span>
                    <span>➔</span>
                  </RouterLink>
                  <button
                    @click="promptDeleteInvoice(inv)"
                    title="Удалить накладную"
                    class="p-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 border border-rose-500/20 rounded-lg text-xs transition-colors cursor-pointer"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!invoices.length">
              <td colspan="8" class="px-6 py-16 text-center text-slate-500 text-sm">
                Накладных не найдено. Загрузите фото или скан накладной, чтобы начать.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Upload Modal -->
    <Transition name="fade">
      <div v-if="showUploadModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-8 w-full max-w-lg shadow-2xl space-y-5">
          <div class="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 class="text-lg font-bold text-white flex items-center gap-2">
              <span>📤</span> Загрузка накладной
            </h3>
            <button @click="closeUploadModal" class="text-slate-400 hover:text-white text-lg">✕</button>
          </div>

          <form @submit.prevent="submitUpload" class="space-y-4">
            <!-- Store Selection -->
            <div>
              <label class="form-label">Склад оприходования (в iiko)</label>
              <select v-model="uploadForm.iiko_store_id" class="form-input" required>
                <option :value="null" disabled>-- Выберите склад оприходования --</option>
                <option v-for="s in stores" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </div>

            <!-- File Input Area -->
            <div>
              <label class="form-label">Файлы накладной (фото, сканы, PDF)</label>
              <input
                type="file"
                ref="fileInputRef"
                multiple
                accept="image/*,application/pdf"
                @change="onFileChange"
                class="hidden"
              />
              <div
                @click="$refs.fileInputRef.click()"
                class="border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-2xl p-6 text-center cursor-pointer transition-colors bg-slate-950/40"
              >
                <div class="text-3xl mb-2">📸</div>
                <p class="text-xs text-white font-semibold">Нажмите для выбора файлов или перетащите сюда</p>
                <p class="text-[11px] text-slate-500 mt-1">Можно выбрать несколько фото одной накладной</p>
              </div>

              <!-- Selected files preview list -->
              <div v-if="uploadFiles.length" class="mt-3 space-y-1.5 max-h-36 overflow-y-auto">
                <div v-for="(f, i) in uploadFiles" :key="i" class="flex items-center justify-between p-2 rounded-lg bg-slate-800/60 text-xs">
                  <span class="truncate max-w-[280px] text-slate-200">Стр. {{ i + 1 }}: {{ f.name }}</span>
                  <button type="button" @click="removeFile(i)" class="text-rose-400 hover:text-rose-300 ml-2">✕</button>
                </div>
              </div>
            </div>

            <div class="flex gap-3 pt-3">
              <button type="button" @click="closeUploadModal"
                class="flex-1 border border-slate-700 text-slate-300 hover:bg-slate-800 py-2.5 rounded-xl text-sm font-medium transition-all">
                Отмена
              </button>
              <button type="submit" :disabled="uploading || !uploadFiles.length"
                class="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2">
                <span v-if="uploading" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>{{ uploading ? 'Отправляем...' : 'Начать распознавание' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>

    <!-- Delete Confirmation Modal -->
    <Transition name="fade">
      <div v-if="invoiceToDelete" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl space-y-4">
          <div class="flex items-center gap-3 text-rose-400">
            <div class="w-11 h-11 rounded-2xl bg-rose-500/15 border border-rose-500/20 flex items-center justify-center text-xl flex-shrink-0">
              🗑️
            </div>
            <div>
              <h3 class="text-base font-bold text-white">Удалить накладную?</h3>
              <p class="text-xs text-slate-400 font-mono mt-0.5">
                {{ invoiceToDelete.invoice_number ? `№ ${invoiceToDelete.invoice_number}` : invoiceToDelete.internal_number }}
              </p>
            </div>
          </div>
          <p class="text-xs text-slate-300 leading-relaxed">
            Вы уверены, что хотите удалить эту накладную? Прикрепленные изображения страниц, позиции товаров и черновик будут удалены безвозвратно.
          </p>
          <div class="flex gap-3 pt-2">
            <button 
              type="button" 
              @click="invoiceToDelete = null" 
              class="flex-1 py-2.5 border border-slate-700 text-slate-300 hover:bg-slate-800 rounded-xl text-xs font-semibold transition-colors"
            >
              Отмена
            </button>
            <button 
              type="button" 
              @click="deleteInvoice" 
              :disabled="deleting" 
              class="flex-1 py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-2"
            >
              <span v-if="deleting" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>{{ deleting ? 'Удаление...' : 'Да, удалить' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const invoices = ref([])
const stores = ref([])
const suppliers = ref([])
const loading = ref(true)
const loadingSuppliers = ref(false)
const isDragging = ref(false)
const showUploadModal = ref(false)
const uploading = ref(false)
const uploadFiles = ref([])
const fileInputRef = ref(null)

const invoiceToDelete = ref(null)
const deleting = ref(false)

// Фильтры
const selectedStatus = ref('')
const invoiceNumberQuery = ref('')
const selectedSupplier = ref(null)
const supplierSearchText = ref('')
const isSupplierDropdownOpen = ref(false)
const supplierDropdownRef = ref(null)

const dateFrom = ref('')
const dateTo = ref('')
const activeDatePreset = ref('')
let searchTimeout = null

const filterStatuses = [
  { value: '', label: 'Все' },
  { value: 'pending', label: 'В очереди' },
  { value: 'processing', label: 'Распознавание (AI)' },
  { value: 'recognized', label: 'Ожидает сверки' },
  { value: 'sent_to_iiko', label: 'Отправлено в iiko' },
  { value: 'failed', label: 'Ошибки' },
]

// Живая фильтрация выпадающего списка поставщиков при вводе текста
const filteredSuppliers = computed(() => {
  const query = supplierSearchText.value.trim().toLowerCase()
  if (!query) {
    return suppliers.value
  }
  return suppliers.value.filter(s => {
    const nameMatch = s.name?.toLowerCase().includes(query)
    const innMatch = s.inn?.toLowerCase().includes(query)
    return nameMatch || innMatch
  })
})

const hasActiveFilters = computed(() => {
  return !!(
    selectedStatus.value ||
    invoiceNumberQuery.value.trim() ||
    supplierSearchText.value.trim() ||
    selectedSupplier.value ||
    dateFrom.value ||
    dateTo.value
  )
})

const activeFiltersCount = computed(() => {
  let count = 0
  if (selectedStatus.value) count++
  if (invoiceNumberQuery.value.trim()) count++
  if (selectedSupplier.value || supplierSearchText.value.trim()) count++
  if (dateFrom.value || dateTo.value) count++
  return count
})

function selectSupplier(sup) {
  selectedSupplier.value = sup
  supplierSearchText.value = sup ? sup.name : ''
  isSupplierDropdownOpen.value = false
  loadInvoices()
}

function clearSupplier() {
  selectedSupplier.value = null
  supplierSearchText.value = ''
  isSupplierDropdownOpen.value = false
  loadInvoices()
}

function handleSupplierInput() {
  isSupplierDropdownOpen.value = true
  if (selectedSupplier.value && selectedSupplier.value.name !== supplierSearchText.value) {
    selectedSupplier.value = null
  }
  debounceSearch()
}

function handleNumberInput() {
  debounceSearch()
}

function clearNumber() {
  invoiceNumberQuery.value = ''
  loadInvoices()
}

function setDatePreset(preset) {
  activeDatePreset.value = preset
  const today = new Date()
  const formatDateISO = (d) => {
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  if (preset === 'today') {
    dateFrom.value = formatDateISO(today)
    dateTo.value = formatDateISO(today)
  } else if (preset === 'week') {
    const past = new Date()
    past.setDate(past.getDate() - 7)
    dateFrom.value = formatDateISO(past)
    dateTo.value = formatDateISO(today)
  } else if (preset === 'month') {
    const past = new Date()
    past.setDate(past.getDate() - 30)
    dateFrom.value = formatDateISO(past)
    dateTo.value = formatDateISO(today)
  } else if (preset === 'this_month') {
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1)
    dateFrom.value = formatDateISO(firstDay)
    dateTo.value = formatDateISO(today)
  } else if (preset === 'all') {
    dateFrom.value = ''
    dateTo.value = ''
  }
  loadInvoices()
}

function handleDateChange() {
  activeDatePreset.value = 'custom'
  loadInvoices()
}

function resetAllFilters() {
  selectedStatus.value = ''
  invoiceNumberQuery.value = ''
  selectedSupplier.value = null
  supplierSearchText.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  activeDatePreset.value = ''
  loadInvoices()
}

function debounceSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadInvoices()
  }, 350)
}

function onDocClick(e) {
  if (supplierDropdownRef.value && !supplierDropdownRef.value.contains(e.target)) {
    isSupplierDropdownOpen.value = false
  }
}

function promptDeleteInvoice(inv) {
  invoiceToDelete.value = inv
}

async function deleteInvoice() {
  if (!invoiceToDelete.value) return
  deleting.value = true
  try {
    await api.delete(`/invoices/documents/${invoiceToDelete.value.id}/`, {
      params: { organization_id: auth.currentOrgId }
    })
    toast.success('Накладная успешно удалена')
    invoices.value = invoices.value.filter(i => i.id !== invoiceToDelete.value.id)
    invoiceToDelete.value = null
  } catch (e) {
    const err = e.response?.data?.error || 'Не удалось удалить накладную'
    toast.error(err)
  } finally {
    deleting.value = false
  }
}

const uploadForm = ref({
  iiko_store_id: null,
  iiko_store_name: '',
})

async function loadInvoices() {
  loading.value = true
  try {
    const params = {
      organization_id: auth.currentOrgId,
      status: selectedStatus.value || undefined,
      number: invoiceNumberQuery.value.trim() || undefined,
      supplier_id: selectedSupplier.value?.id || undefined,
      supplier: (selectedSupplier.value?.name || supplierSearchText.value.trim()) || undefined,
      date_from: dateFrom.value || undefined,
      date_to: dateTo.value || undefined,
    }
    const res = await api.get('/invoices/documents/', { params })
    invoices.value = res.data.results || res.data || []
  } catch (e) {
    toast.error('Не удалось загрузить накладные')
  } finally {
    loading.value = false
  }
}

async function loadStores() {
  try {
    const res = await api.get('/invoices/stores/', { params: { organization_id: auth.currentOrgId } })
    stores.value = res.data || []
    const org = auth.currentMembership?.organization
    if (org?.default_store_id) {
      uploadForm.value.iiko_store_id = org.default_store_id
    } else if (stores.value.length) {
      uploadForm.value.iiko_store_id = stores.value[0].id
    }
  } catch (e) {
    console.warn('Could not load stores:', e)
  }
}

async function loadSuppliers() {
  loadingSuppliers.value = true
  try {
    const res = await api.get('/invoices/suppliers/', {
      params: { organization_id: auth.currentOrgId }
    })
    suppliers.value = res.data || []
  } catch (e) {
    console.warn('Could not load suppliers:', e)
  } finally {
    loadingSuppliers.value = false
  }
}

function onFileChange(e) {
  const files = Array.from(e.target.files || [])
  uploadFiles.value.push(...files)
}

function handleFileDrop(e) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files || [])
  if (files.length) {
    uploadFiles.value.push(...files)
    showUploadModal.value = true
  }
}

function removeFile(index) {
  uploadFiles.value.splice(index, 1)
}

function closeUploadModal() {
  showUploadModal.value = false
  uploadFiles.value = []
}

async function submitUpload() {
  if (!uploadFiles.value.length) {
    toast.error('Выберите хотя бы один файл накладной')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('organization_id', auth.currentOrgId)
    formData.append('source', 'web_admin')
    
    if (uploadForm.value.iiko_store_id) {
      formData.append('iiko_store_id', uploadForm.value.iiko_store_id)
      const st = stores.value.find(s => String(s.id) === String(uploadForm.value.iiko_store_id))
      if (st) formData.append('iiko_store_name', st.name)
    }

    uploadFiles.value.forEach((file) => {
      formData.append('files', file)
    })

    const res = await api.post('/invoices/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    toast.success('Накладная загружена и отправлена на AI-распознавание!')
    closeUploadModal()
    router.push(`/admin/invoices/${res.data.id}`)
  } catch (e) {
    const err = e.response?.data?.error || 'Ошибка при загрузке файлов'
    toast.error(err)
  } finally {
    uploading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ru-RU')
}

function statusBadgeClass(status) {
  switch (status) {
    case 'sent_to_iiko':
      return 'bg-emerald-950/50 text-emerald-300 border-emerald-800'
    case 'recognized':
      return 'bg-amber-950/50 text-amber-300 border-amber-800'
    case 'processing':
      return 'bg-indigo-950/50 text-indigo-300 border-indigo-800'
    case 'failed':
      return 'bg-rose-950/50 text-rose-300 border-rose-800'
    default:
      return 'bg-slate-800 text-slate-300 border-slate-700'
  }
}

function statusDotClass(status) {
  switch (status) {
    case 'sent_to_iiko':
      return 'bg-emerald-400'
    case 'recognized':
      return 'bg-amber-400'
    case 'processing':
      return 'bg-indigo-400 animate-pulse'
    case 'failed':
      return 'bg-rose-400'
    default:
      return 'bg-slate-400'
  }
}

onMounted(() => {
  loadInvoices()
  loadStores()
  loadSuppliers()
  document.addEventListener('click', onDocClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  if (searchTimeout) clearTimeout(searchTimeout)
})
</script>
