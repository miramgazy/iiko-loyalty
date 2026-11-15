<template>
  <div class="min-h-screen relative flex flex-col page-p overflow-x-hidden">
    <!-- Ambient gold background glow -->
    <div class="absolute w-[240px] h-[240px] rounded-full -top-[60px] -right-[40px] pointer-events-none opacity-20"
         style="background: radial-gradient(circle, var(--gold) 0%, transparent 70%);"></div>

    <!-- Header Card -->
    <div class="card-luxury p-4 text-left shadow-sm mb-4 z-10" style="margin-bottom: 16px;">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-lg font-black text-[color:var(--text)] tracking-tight">Загрузка накладной</h1>
          <p class="text-xs text-[color:var(--muted)] font-medium mt-0.5">Приемка товаров и запуск AI</p>
        </div>
        <div v-if="filesList.length > 0" class="px-2.5 py-1 rounded-full text-xs font-black bg-[color:var(--gold)]/15 text-[color:var(--gold)] border border-[color:var(--gold)]/30">
          {{ filesList.length }} {{ filesCountWord(filesList.length) }}
        </div>
      </div>
    </div>

    <!-- SUCCESS STATE OVERLAY -->
    <div v-if="uploadSuccess" class="flex-1 flex flex-col items-center justify-center text-center z-20 py-8">
      <div class="w-20 h-20 rounded-full bg-green-500/15 border-2 border-green-500/30 flex items-center justify-center text-green-400 text-4xl mb-4 shadow-lg">
        ✓
      </div>
      <h2 class="text-xl font-black text-[color:var(--text)] mb-2">Накладная отправлена!</h2>
      <p class="text-xs text-[color:var(--muted)] max-w-xs mb-3">
        Номер документа: <span class="font-extrabold text-[color:var(--gold)] font-mono">{{ createdDocNumber }}</span>
      </p>
      <div class="card-luxury p-4 text-xs text-[color:var(--muted)] max-w-xs mb-6 text-left border border-[color:var(--border)]">
        <div class="flex items-start gap-2 mb-2">
          <span class="text-base">🤖</span>
          <span>AI извлекает товары, фасовку и суммы из {{ uploadedPagesCount }} {{ filesCountWord(uploadedPagesCount) }}.</span>
        </div>
        <div class="flex items-start gap-2">
          <span class="text-base">👩‍💼</span>
          <span>Бухгалтер проверит сопоставление и создаст приход в iiko.</span>
        </div>
      </div>

      <div class="flex flex-col gap-3 w-full max-w-xs">
        <button 
          @click="resetForm"
          class="btn-primary w-full py-3 text-xs flex items-center justify-center gap-2"
        >
          <span>📸 Загрузить еще одну накладную</span>
        </button>
        <button 
          @click="$router.push('/employee/invoices')"
          class="w-full py-3 rounded-xl font-bold text-xs bg-[color:var(--bg-secondary)] border border-[color:var(--border)] text-[color:var(--text)] active:scale-95 transition-all cursor-pointer"
        >
          <span>📋 К списку накладных</span>
        </button>
      </div>
    </div>

    <!-- MAIN FORM VIEW -->
    <div v-else class="flex flex-col z-10">
      <!-- 1. Auto-generated Draft Number Card -->
      <div class="card-luxury p-4 flex items-center justify-between mb-4 text-left">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-[color:var(--bg-secondary)] border border-[color:var(--border)] flex items-center justify-center text-xl flex-shrink-0">
            🧾
          </div>
          <div class="flex flex-col">
            <span class="sheet-label" style="margin-bottom: 2px;">Номер черновика</span>
            <span class="text-sm font-extrabold text-[color:var(--text)] tracking-tight font-mono">
              {{ autoDocNumber }}
            </span>
          </div>
        </div>
        <span class="text-[10px] px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-400 font-bold border border-blue-500/20">
          Черновик
        </span>
      </div>

      <!-- 2. Warehouse / Store Selector -->
      <div class="card-luxury p-4 flex flex-col gap-2 text-left mb-4">
        <label class="sheet-label flex items-center justify-between">
          <span>Склад оприходования в iiko</span>
          <span v-if="loadingStores" class="text-[10px] text-[color:var(--muted)] normal-case font-normal flex items-center gap-1">
            <span class="w-2.5 h-2.5 border-2 border-[color:var(--gold)]/30 border-t-[color:var(--gold)] rounded-full animate-spin"></span>
            загрузка складов...
          </span>
        </label>
        
        <div class="relative w-full">
          <select 
            v-model="selectedStoreId" 
            class="sheet-input appearance-none pr-10 cursor-pointer"
          >
            <option value="" disabled>-- Выберите склад iiko --</option>
            <option v-for="st in stores" :key="st.id" :value="String(st.id)">
              {{ st.name }}
            </option>
          </select>
          <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3.5 text-[color:var(--muted)]">
            <svg class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
        <span class="text-[11px] text-[color:var(--muted)]">
          {{ selectedStoreName ? `Выбран: ${selectedStoreName}` : 'Выберите склад, куда фактически поступает товар' }}
        </span>
      </div>

      <!-- 3. Photo Capture & Files Section -->
      <div class="card-luxury p-4 flex flex-col gap-3 text-left mb-4">
        <div class="flex items-center justify-between">
          <label class="sheet-label" style="margin-bottom: 0;">
            Фотографии страниц накладной
          </label>
          <span class="text-[10px] text-[color:var(--muted)] font-bold">
            Все страницы одного документа
          </span>
        </div>

        <!-- Hidden inputs -->
        <input 
          ref="cameraInputRef" 
          type="file" 
          accept="image/*" 
          capture="environment" 
          class="hidden" 
          @change="handleFileInputChange" 
        />
        <input 
          ref="galleryInputRef" 
          type="file" 
          accept="image/*,application/pdf" 
          multiple 
          class="hidden" 
          @change="handleFileInputChange" 
        />

        <!-- Action Upload Buttons -->
        <div class="grid grid-cols-2 gap-3">
          <!-- Camera Button -->
          <button 
            type="button"
            @click="openCamera"
            class="py-3 px-3 rounded-xl border border-[color:var(--gold)]/40 bg-[color:var(--gold)]/10 text-[color:var(--gold)] font-extrabold text-xs flex items-center justify-center gap-2 active:scale-95 transition-all cursor-pointer shadow-sm"
          >
            <svg class="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
            <span>Камера (фото)</span>
          </button>

          <!-- Gallery / PDF Button -->
          <button 
            type="button"
            @click="openGallery"
            class="py-3 px-3 rounded-xl border border-[color:var(--border)] bg-[color:var(--bg-secondary)] text-[color:var(--text)] font-extrabold text-xs flex items-center justify-center gap-2 active:scale-95 transition-all cursor-pointer shadow-sm"
          >
            <svg class="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
            <span>Галерея / PDF</span>
          </button>
        </div>

        <!-- Instruction Hint -->
        <p class="text-[11px] text-[color:var(--muted)] leading-relaxed">
          Делайте четкие снимки при хорошем освещении. Если накладная состоит из нескольких страниц, сфотографируйте их по порядку.
        </p>

        <!-- Pages Thumbnails Carousel / Grid -->
        <div v-if="filesList.length > 0" class="flex flex-col gap-2 pt-2">
          <div class="flex items-center justify-between text-xs font-bold text-[color:var(--text)]">
            <span>Добавленные страницы ({{ filesList.length }})</span>
            <button 
              type="button" 
              @click="clearAllFiles" 
              class="text-[11px] text-red-400 font-bold hover:underline"
            >
              Очистить все
            </button>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div 
              v-for="(item, idx) in filesList" 
              :key="idx"
              class="relative rounded-xl overflow-hidden border border-[color:var(--border)] bg-[color:var(--bg-secondary)] flex flex-col group shadow-sm"
            >
              <!-- Thumbnail container -->
              <div class="h-32 w-full bg-black/25 flex items-center justify-center overflow-hidden relative">
                <!-- If PDF -->
                <div v-if="item.isPdf" class="flex flex-col items-center justify-center text-red-400 p-2 text-center">
                  <span class="text-3xl mb-1">📄</span>
                  <span class="text-[10px] font-mono text-[color:var(--text)] truncate max-w-full px-1">{{ item.file.name }}</span>
                </div>
                <!-- If Image -->
                <img 
                  v-else 
                  :src="item.previewUrl" 
                  alt="Page preview" 
                  class="w-full h-full object-cover cursor-pointer"
                  @click="openPreview(item.previewUrl)"
                />

                <!-- Page number badge -->
                <div class="absolute top-2 left-2 bg-black/75 backdrop-blur-xs text-white text-[10px] font-black px-2 py-0.5 rounded-md">
                  Стр. {{ idx + 1 }}
                </div>

                <!-- Delete button -->
                <button 
                  type="button"
                  @click="removeFile(idx)"
                  class="absolute top-2 right-2 w-6 h-6 rounded-full bg-red-500/85 text-white flex items-center justify-center text-xs active:scale-90 transition-transform cursor-pointer shadow-md"
                  title="Удалить"
                >
                  ✕
                </button>
              </div>

              <!-- Footer with file size -->
              <div class="p-2 text-[10px] text-[color:var(--muted)] flex items-center justify-between bg-[color:var(--bg-secondary)]">
                <span class="truncate max-w-[85px]">{{ item.file.name }}</span>
                <span class="font-mono">{{ formatFileSize(item.file.size) }}</span>
              </div>
            </div>

            <!-- Add next page tile -->
            <button 
              type="button"
              @click="openCamera"
              class="h-32 rounded-xl border-2 border-dashed border-[color:var(--gold)]/40 hover:border-[color:var(--gold)] bg-[color:var(--gold)]/5 flex flex-col items-center justify-center gap-1.5 text-[color:var(--gold)] active:scale-95 transition-all cursor-pointer"
            >
              <span class="text-3xl font-light leading-none">+</span>
              <span class="text-xs font-bold text-center px-2">Добавить страницу</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Error banner if any -->
      <div v-if="submitError" class="p-3.5 rounded-xl bg-red-500/15 border border-red-500/30 text-red-400 text-xs font-semibold mb-4 text-left">
        {{ submitError }}
      </div>

      <!-- Submit Button -->
      <div class="mb-4">
        <button 
          type="button"
          @click="submitInvoice"
          :disabled="isSubmitting || filesList.length === 0"
          class="btn-primary w-full flex items-center justify-center gap-2"
          :class="{
            'opacity-50 cursor-not-allowed': isSubmitting || filesList.length === 0,
          }"
        >
          <span v-if="isSubmitting" class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin"></span>
          <template v-else>
            <svg class="w-5 h-5 stroke-current fill-none" viewBox="0 0 24 24" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
            <span>
              {{ filesList.length === 0 ? 'Сделайте фото для отправки' : `Отправить накладную (${filesList.length} стр.)` }}
            </span>
          </template>
        </button>
      </div>

      <!-- Return to regular client card tile -->
      <div class="mb-4">
        <div @click="$router.push('/')" 
             class="card-luxury flex justify-between items-center p-4 cursor-pointer transition-all duration-300 active:scale-[0.98] hover:scale-[1.01]"
             style="background: linear-gradient(135deg, rgba(201, 168, 76, 0.12) 0%, rgba(201, 168, 76, 0.03) 100%); border-color: rgba(201, 168, 76, 0.25); margin-bottom: 0;">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center bg-white/10" style="color: var(--gold)">
              <svg class="w-5 h-5 stroke-current" viewBox="0 0 24 24" fill="none" stroke-width="2">
                <rect x="2" y="5" width="20" height="14" rx="2" />
                <line x1="2" y1="10" x2="22" y2="10" />
              </svg>
            </div>
            <div class="flex flex-col text-left">
              <span class="text-[14px] font-extrabold text-[color:var(--text)] leading-tight">
                Карта гостя
              </span>
              <span class="text-[10px] text-[color:var(--muted)] font-bold">
                Перейти к карте лояльности
              </span>
            </div>
          </div>
          <svg class="w-5 h-5" style="color: var(--gold); opacity: 0.7;" viewBox="0 0 24 24" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- FULLSCREEN IMAGE PREVIEW MODAL -->
    <div 
      v-if="previewModalUrl" 
      class="fixed inset-0 bg-black/90 z-50 flex flex-col p-4 backdrop-blur-sm"
      @click="previewModalUrl = null"
    >
      <div class="flex items-center justify-end pb-3">
        <button 
          @click="previewModalUrl = null" 
          class="w-9 h-9 rounded-full bg-white/20 text-white flex items-center justify-center text-sm font-bold"
        >
          ✕
        </button>
      </div>
      <div class="flex-1 flex items-center justify-center overflow-auto">
        <img :src="previewModalUrl" alt="Full preview" class="max-w-full max-h-full object-contain rounded-lg" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api'

const router = useRouter()
const auth = useAuthStore()

const cameraInputRef = ref(null)
const galleryInputRef = ref(null)

const filesList = ref([])
const stores = ref([])
const loadingStores = ref(false)
const selectedStoreId = ref('')

const isSubmitting = ref(false)
const submitError = ref(null)
const uploadSuccess = ref(false)
const createdDocNumber = ref('')
const uploadedPagesCount = ref(0)
const previewModalUrl = ref(null)

// Client-side auto doc number preview: НАКЛ-YYYYMMDD-XXXX
const autoDocNumber = ref(generateAutoNumber())

function generateAutoNumber() {
  const d = new Date()
  const ymd = d.toISOString().slice(0, 10).replace(/-/g, '')
  const rand = Math.floor(1000 + Math.random() * 9000)
  return `НАКЛ-${ymd}-${rand}`
}

const selectedStoreName = computed(() => {
  const st = stores.value.find(s => String(s.id) === String(selectedStoreId.value))
  return st?.name || ''
})

function triggerHaptic(type = 'impact', subtype = 'light') {
  const tg = window.Telegram?.WebApp
  if (tg?.HapticFeedback) {
    if (type === 'impact') {
      tg.HapticFeedback.impactOccurred(subtype)
    } else if (type === 'notification') {
      tg.HapticFeedback.notificationOccurred(subtype)
    } else if (type === 'selection') {
      tg.HapticFeedback.selectionChanged()
    }
  }
}

function openCamera() {
  triggerHaptic('impact', 'light')
  cameraInputRef.value?.click()
}

function openGallery() {
  triggerHaptic('impact', 'light')
  galleryInputRef.value?.click()
}

function handleFileInputChange(e) {
  const files = e.target.files
  if (!files || files.length === 0) return

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    let previewUrl = null
    if (!isPdf) {
      previewUrl = URL.createObjectURL(file)
    }
    filesList.value.push({
      file,
      isPdf,
      previewUrl,
    })
  }

  // Reset input values so same file can be re-selected if needed
  if (cameraInputRef.value) cameraInputRef.value.value = ''
  if (galleryInputRef.value) galleryInputRef.value.value = ''

  triggerHaptic('notification', 'success')
}

function removeFile(idx) {
  triggerHaptic('impact', 'light')
  const item = filesList.value[idx]
  if (item?.previewUrl) {
    URL.revokeObjectURL(item.previewUrl)
  }
  filesList.value.splice(idx, 1)
}

function clearAllFiles() {
  triggerHaptic('impact', 'medium')
  filesList.value.forEach(item => {
    if (item.previewUrl) URL.revokeObjectURL(item.previewUrl)
  })
  filesList.value = []
}

function openPreview(url) {
  if (!url) return
  triggerHaptic('impact', 'light')
  previewModalUrl.value = url
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(0)} KB`
  return `${(kb / 1024).toFixed(1)} MB`
}

function filesCountWord(count) {
  if (count % 10 === 1 && count % 100 !== 11) return 'страница'
  if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) return 'страницы'
  return 'страниц'
}

async function loadStores() {
  loadingStores.value = true
  try {
    const orgId = auth.organization?.id
    let res
    try {
      res = await api.get('/invoices/stores/', { params: { organization_id: orgId } })
    } catch (e1) {
      res = await api.get('/invoices/iiko/stores/', { params: { organization_id: orgId } })
    }
    stores.value = res.data || []

    // Preselect defaultStore from organization if available
    const defStore = auth.organization?.default_store_id
    if (defStore && stores.value.some(s => String(s.id) === String(defStore))) {
      selectedStoreId.value = String(defStore)
    } else if (stores.value.length > 0) {
      selectedStoreId.value = String(stores.value[0].id)
    }
  } catch (e) {
    console.error('Error fetching stores:', e)
  } finally {
    loadingStores.value = false
  }
}

async function submitInvoice() {
  if (filesList.value.length === 0) {
    submitError.value = 'Пожалуйста, добавьте хотя бы одну страницу накладной'
    return
  }

  isSubmitting.value = true
  submitError.value = null
  triggerHaptic('impact', 'medium')

  try {
    const formData = new FormData()
    formData.append('source', 'tma')
    if (auth.organization?.id) {
      formData.append('organization_id', auth.organization.id)
    }
    if (selectedStoreId.value) {
      formData.append('iiko_store_id', selectedStoreId.value)
    }
    if (selectedStoreName.value) {
      formData.append('iiko_store_name', selectedStoreName.value)
    }

    // Append each file
    filesList.value.forEach(item => {
      formData.append('files', item.file)
    })

    const res = await api.post('/invoices/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    })

    createdDocNumber.value = res.data.internal_number || autoDocNumber.value
    uploadedPagesCount.value = filesList.value.length
    uploadSuccess.value = true
    triggerHaptic('notification', 'success')
  } catch (e) {
    console.error('Upload error:', e)
    submitError.value = e.response?.data?.error || 'Ошибка при загрузке накладной. Попробуйте еще раз.'
    triggerHaptic('notification', 'error')
  } finally {
    isSubmitting.value = false
  }
}

function resetForm() {
  clearAllFiles()
  uploadSuccess.value = false
  submitError.value = null
  autoDocNumber.value = generateAutoNumber()
  triggerHaptic('impact', 'light')
}

onMounted(() => {
  loadStores()
})
</script>
