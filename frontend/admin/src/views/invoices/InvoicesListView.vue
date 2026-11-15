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

    <!-- Filters & Search -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div class="flex items-center gap-2 overflow-x-auto pb-1">
        <button
          v-for="st in filterStatuses"
          :key="st.value"
          @click="selectedStatus = st.value; loadInvoices()"
          class="px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all"
          :class="selectedStatus === st.value
            ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
            : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-850'"
        >
          {{ st.label }}
        </button>
      </div>

      <div class="relative w-full md:w-72">
        <input
          v-model="searchQuery"
          @input="debounceSearch"
          type="text"
          placeholder="Поиск по номеру, поставщику..."
          class="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
        <span class="absolute right-3 top-2.5 text-slate-500 text-xs">🔍</span>
      </div>
    </div>

    <!-- Invoices Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>

      <table v-else class="w-full text-left text-sm text-slate-300">
        <thead>
          <tr class="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider bg-slate-950/40">
            <th class="px-6 py-4">Документ</th>
            <th class="px-6 py-4">Поставщик</th>
            <th class="px-6 py-4">Склад iiko</th>
            <th class="px-6 py-4">Сумма</th>
            <th class="px-6 py-4">Статус</th>
            <th class="px-6 py-4">Источник</th>
            <th class="px-6 py-4 text-right">Действия</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="inv in invoices" :key="inv.id" class="hover:bg-slate-850/50 transition-colors">
            <td class="px-6 py-4">
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
            <td class="px-6 py-4">
              <p class="font-medium text-white">{{ inv.iiko_supplier_name || inv.raw_supplier_name || '—' }}</p>
              <p v-if="inv.raw_supplier_inn" class="text-[11px] text-slate-500 font-mono">ИНН: {{ inv.raw_supplier_inn }}</p>
            </td>
            <td class="px-6 py-4">
              <span class="text-xs text-slate-300">{{ inv.iiko_store_name || 'Не выбран' }}</span>
            </td>
            <td class="px-6 py-4 font-mono font-bold text-white">
              {{ inv.total_sum ? Number(inv.total_sum).toLocaleString('ru-RU', { minimumFractionDigits: 2 }) + ' ₸' : '—' }}
            </td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full border"
                :class="statusBadgeClass(inv.status)">
                <span class="w-1.5 h-1.5 rounded-full" :class="statusDotClass(inv.status)"></span>
                {{ inv.status_display }}
              </span>
            </td>
            <td class="px-6 py-4 text-xs text-slate-400">
              <span class="px-2 py-0.5 rounded bg-slate-800 font-mono text-[11px]">
                {{ inv.source === 'tma' ? '📱 TMA' : '💻 Админка' }}
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <RouterLink :to="`/admin/invoices/${inv.id}`"
                class="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded-lg text-xs font-semibold transition-all inline-flex items-center gap-1.5">
                <span>Открыть</span>
                <span>➔</span>
              </RouterLink>
            </td>
          </tr>
          <tr v-if="!invoices.length">
            <td colspan="7" class="px-6 py-16 text-center text-slate-500 text-sm">
              Накладных не найдено. Загрузите фото или скан накладной, чтобы начать.
            </td>
          </tr>
        </tbody>
      </table>
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const router = useRouter()
const auth = useAuthStore()
const toast = useToastStore()

const invoices = ref([])
const stores = ref([])
const loading = ref(true)
const isDragging = ref(false)
const showUploadModal = ref(false)
const uploading = ref(false)
const uploadFiles = ref([])
const fileInputRef = ref(null)

const uploadForm = ref({
  iiko_store_id: null,
  iiko_store_name: '',
})

const selectedStatus = ref('')
const searchQuery = ref('')
let searchTimeout = null

const filterStatuses = [
  { value: '', label: 'Все' },
  { value: 'pending', label: 'В очереди' },
  { value: 'processing', label: 'Распознавание (AI)' },
  { value: 'recognized', label: 'Ожидает сверки' },
  { value: 'sent_to_iiko', label: 'Отправлено в iiko' },
  { value: 'failed', label: 'Ошибки' },
]

async function loadInvoices() {
  loading.value = true
  try {
    const params = {
      organization_id: auth.currentOrgId,
      status: selectedStatus.value || undefined,
      search: searchQuery.value || undefined
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

function debounceSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadInvoices()
  }, 400)
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
})
</script>
