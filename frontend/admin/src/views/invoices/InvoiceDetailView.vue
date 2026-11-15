<template>
  <div class="h-[calc(100vh-2rem)] flex flex-col p-6 space-y-4 overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-2xl px-6 py-4 flex-shrink-0">
      <div class="flex items-center gap-4">
        <button @click="$router.push('/admin/invoices')"
          class="w-9 h-9 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition-colors">
          ‹
        </button>
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-lg font-bold text-white">
              Накладная {{ invoice?.invoice_number || invoice?.internal_number }}
            </h1>
            <span class="text-xs px-2.5 py-0.5 rounded-full border font-medium" :class="statusBadgeClass(invoice?.status)">
              {{ invoice?.status_display }}
            </span>
            <span v-if="invoice?.iiko_document_number" class="text-xs font-mono text-emerald-400 bg-emerald-950/50 border border-emerald-800 px-2 py-0.5 rounded">
              iiko № {{ invoice.iiko_document_number }}
            </span>
          </div>
          <p class="text-xs text-slate-400 mt-0.5">
            {{ invoice?.raw_supplier_name || 'Поставщик не определен' }} • Создан {{ formatDate(invoice?.created_at) }}
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-3">
        <button
          @click="reprocessInvoice"
          :disabled="reprocessing || invoice?.status === 'processing'"
          class="px-3.5 py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 disabled:opacity-50"
        >
          <span>↻</span>
          <span>{{ reprocessing ? 'Запуск...' : 'Перераспознать (AI)' }}</span>
        </button>

        <button
          v-if="invoice?.status !== 'sent_to_iiko'"
          @click="sendToIiko"
          :disabled="sendingToIiko || invoice?.status === 'processing' || hasUnmatchedItems"
          class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2"
        >
          <span v-if="sendingToIiko" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          <span>🚀 Создать накладную в iiko (Черновик)</span>
        </button>
      </div>
    </div>

    <!-- Error Banner if any -->
    <div v-if="invoice?.error_message" class="p-3.5 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center justify-between flex-shrink-0">
      <div class="flex items-center gap-2">
        <span>⚠️</span>
        <span>{{ invoice.error_message }}</span>
      </div>
      <button @click="reprocessInvoice" class="underline hover:text-white">Повторить попытку</button>
    </div>

    <!-- Split View Content -->
    <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0 overflow-hidden">
      <!-- LEFT: Image Preview Viewer (5 cols) -->
      <div class="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden">
        <!-- Viewer Toolbar -->
        <div class="px-4 py-2.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div class="flex items-center gap-2">
            <span class="font-semibold text-slate-200">Страница {{ currentImageIndex + 1 }} из {{ images.length }}</span>
            <div class="flex gap-1 ml-2">
              <button
                v-for="(_, idx) in images"
                :key="idx"
                @click="currentImageIndex = idx"
                class="w-6 h-6 rounded flex items-center justify-center font-mono text-[11px] transition-colors"
                :class="currentImageIndex === idx ? 'bg-indigo-600 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-400'"
              >
                {{ idx + 1 }}
              </button>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button @click="zoomOut" class="w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center font-bold">-</button>
            <span class="font-mono text-[11px] w-12 text-center">{{ Math.round(zoomLevel * 100) }}%</span>
            <button @click="zoomIn" class="w-6 h-6 rounded bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center font-bold">+</button>
            <button @click="resetZoom" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[10px]">Сброс</button>
          </div>
        </div>

        <!-- Image Container -->
        <div class="flex-1 overflow-auto p-4 flex items-center justify-center bg-slate-950/80 relative">
          <div v-if="currentImage" class="transition-transform duration-150 origin-center" :style="{ transform: `scale(${zoomLevel})` }">
            <img :src="currentImage.image_url" :alt="`Страница ${currentImageIndex + 1}`" class="max-w-full rounded shadow-2xl" />
          </div>
          <div v-else class="text-slate-500 text-xs">Нет изображений для предпросмотра</div>
        </div>
      </div>

      <!-- RIGHT: Interactive Metadata & Items Table (7 cols) -->
      <div class="lg:col-span-7 flex flex-col space-y-4 overflow-hidden">
        <!-- Document Meta Card -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 grid grid-cols-1 md:grid-cols-4 gap-3 flex-shrink-0 text-xs">
          <!-- Supplier -->
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Поставщик в iiko</label>
            <div class="flex gap-1.5">
              <select v-model="invoice.iiko_supplier_id" @change="saveHeader" class="form-input text-xs py-1.5 flex-1">
                <option :value="null">-- Не выбран --</option>
                <option v-for="sup in suppliers" :key="sup.id" :value="sup.id">{{ sup.name }}</option>
              </select>
              <button @click="showSupplierModal = true" title="Создать контрагента в iiko"
                class="px-2 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-bold">
                +
              </button>
            </div>
          </div>

          <!-- Store -->
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Склад оприходования</label>
            <select v-model="invoice.iiko_store_id" @change="onStoreChange" class="form-input text-xs py-1.5">
              <option :value="null">-- Не выбран --</option>
              <option v-for="st in stores" :key="st.id" :value="st.id">{{ st.name }}</option>
            </select>
          </div>

          <!-- Number -->
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Номер накладной</label>
            <input v-model="invoice.invoice_number" @blur="saveHeader" type="text" class="form-input text-xs py-1.5" placeholder="Номер..." />
          </div>

          <!-- Date -->
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Дата накладной</label>
            <input v-model="invoice.invoice_date" @blur="saveHeader" type="date" class="form-input text-xs py-1.5" />
          </div>
        </div>

        <!-- Items Table Container -->
        <div class="flex-1 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl">
          <!-- Table Header / Summary -->
          <div class="px-5 py-3 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs flex-shrink-0">
            <div class="flex items-center gap-3">
              <span class="font-bold text-white">Товарные позиции ({{ items.length }})</span>
              <div class="flex items-center gap-2 text-[11px]">
                <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/60">🟢 {{ countByStatus('green') }} точно</span>
                <span class="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800/60">🟡 {{ countByStatus('yellow') }} похоже</span>
                <span class="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800/60">🔴 {{ countByStatus('red') }} не найдено</span>
              </div>
            </div>

            <div class="flex items-center gap-4 text-xs font-mono">
              <div class="text-right">
                <span class="text-slate-400 text-[11px]">Сумма документа: </span>
                <span class="text-white font-bold">{{ totalCalculatedSum.toLocaleString('ru-RU', { minimumFractionDigits: 2 }) }} ₸</span>
              </div>
            </div>
          </div>

          <!-- Scrollable Table -->
          <div class="flex-1 overflow-auto">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="sticky top-0 bg-slate-900 border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider z-10">
                <tr>
                  <th class="px-3 py-2.5 w-8">#</th>
                  <th class="px-3 py-2.5">Из накладной (Фото)</th>
                  <th class="px-3 py-2.5 w-60">Товар в iiko</th>
                  <th class="px-3 py-2.5 text-right w-20">Кол-во</th>
                  <th class="px-3 py-2.5 text-center w-28">Коэф. фасовки</th>
                  <th class="px-3 py-2.5 text-right w-24">В iiko (баз.)</th>
                  <th class="px-3 py-2.5 text-right w-24">Цена iiko</th>
                  <th class="px-3 py-2.5 text-right w-24">Сумма</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-800/60">
                <tr v-for="item in items" :key="item.id"
                  class="hover:bg-slate-850/60 transition-colors"
                  :class="{
                    'bg-emerald-950/10': item.match_status === 'green',
                    'bg-amber-950/10': item.match_status === 'yellow',
                    'bg-rose-950/10': item.match_status === 'red',
                  }"
                >
                  <td class="px-3 py-2 text-slate-500 font-mono text-[11px]">{{ item.num }}</td>
                  
                  <!-- Raw name from invoice -->
                  <td class="px-3 py-2">
                    <p class="font-medium text-white text-xs leading-snug">{{ item.raw_name }}</p>
                    <p class="text-[10px] text-slate-500 mt-0.5">
                      {{ item.raw_amount }} {{ item.raw_unit }} • по {{ item.raw_price }} ₸
                    </p>
                  </td>

                  <!-- iiko Product selection -->
                  <td class="px-3 py-2">
                    <div class="space-y-1">
                      <div class="flex items-center gap-1.5">
                        <span class="text-sm">
                          {{ item.match_status === 'green' ? '🟢' : item.match_status === 'yellow' ? '🟡' : '🔴' }}
                        </span>
                        <div class="flex-1 relative">
                          <input
                            type="text"
                            :value="item.iiko_product_name"
                            @focus="openSearchFor(item)"
                            readonly
                            placeholder="Выберите товар iiko..."
                            class="form-input text-xs py-1 px-2 cursor-pointer w-full"
                            :class="item.iiko_product_id ? 'text-slate-100 font-medium' : 'text-rose-400 border-rose-800/80'"
                          />
                        </div>
                      </div>
                    </div>
                  </td>

                  <!-- Raw Amount -->
                  <td class="px-3 py-2 text-right font-mono font-medium text-slate-200">
                    {{ item.raw_amount }} {{ item.raw_unit }}
                  </td>

                  <!-- Packaging Coefficient -->
                  <td class="px-3 py-2 text-center">
                    <div class="inline-flex items-center gap-1">
                      <input
                        type="number"
                        step="0.001"
                        min="0.001"
                        v-model.number="item.packaging_coefficient"
                        @change="updateItemValues(item)"
                        class="w-16 bg-slate-800 border border-slate-700 rounded px-1.5 py-0.5 text-center font-mono text-xs text-white focus:border-indigo-500 focus:outline-none"
                      />
                    </div>
                  </td>

                  <!-- iiko Base Amount -->
                  <td class="px-3 py-2 text-right font-mono font-bold text-white">
                    {{ item.iiko_amount }}
                  </td>

                  <!-- iiko Price per base unit -->
                  <td class="px-3 py-2 text-right font-mono text-slate-300">
                    {{ item.iiko_price }} ₸
                  </td>

                  <!-- Sum -->
                  <td class="px-3 py-2 text-right font-mono font-bold text-white">
                    {{ Number(item.iiko_sum).toLocaleString('ru-RU', { minimumFractionDigits: 2 }) }} ₸
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Product Live Search Modal -->
    <Transition name="fade">
      <div v-if="searchModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
          <div class="flex items-center justify-between pb-2 border-b border-slate-800">
            <div>
              <h3 class="text-sm font-bold text-white">Сопоставить с товаром iiko</h3>
              <p class="text-[11px] text-slate-400 truncate max-w-sm">Исходное: {{ activeSearchItem?.raw_name }}</p>
            </div>
            <button @click="searchModalOpen = false" class="text-slate-400 hover:text-white">✕</button>
          </div>

          <div>
            <input
              v-model="catalogQuery"
              @input="searchCatalog"
              type="text"
              placeholder="Поиск по названию или коду в iiko..."
              class="form-input text-xs"
              autofocus
            />
          </div>

          <div class="max-h-64 overflow-y-auto space-y-1">
            <div
              v-for="prod in catalogResults"
              :key="prod.id"
              @click="selectProductForActiveItem(prod)"
              class="p-2.5 rounded-xl bg-slate-800/40 hover:bg-indigo-600/20 hover:border-indigo-500/40 border border-transparent cursor-pointer transition-all flex items-center justify-between text-xs"
            >
              <div>
                <p class="text-white font-medium">{{ prod.name }}</p>
                <p class="text-[10px] text-slate-500 font-mono">Код: {{ prod.code || '—' }} • Баз. ед: {{ prod.unit || 'кг' }}</p>
              </div>
              <span class="text-indigo-400 text-xs">Выбрать ➔</span>
            </div>
            <div v-if="!catalogResults.length" class="text-center py-6 text-slate-500 text-xs">
              Товары не найдены
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Create Supplier Modal -->
    <Transition name="fade">
      <div v-if="showSupplierModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl space-y-4">
          <div class="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 class="text-sm font-bold text-white">Создать контрагента в iiko</h3>
            <button @click="showSupplierModal = false" class="text-slate-400 hover:text-white">✕</button>
          </div>

          <form @submit.prevent="createSupplierInIiko" class="space-y-3 text-xs">
            <div>
              <label class="form-label">Наименование поставщика</label>
              <input v-model="newSupplierForm.name" type="text" class="form-input text-xs" required />
            </div>
            <div>
              <label class="form-label">ИНН / БИН</label>
              <input v-model="newSupplierForm.inn" type="text" class="form-input text-xs" />
            </div>
            <div>
              <label class="form-label">Артикул / Код (опционально)</label>
              <input v-model="newSupplierForm.code" type="text" class="form-input text-xs" />
            </div>
            <div class="flex gap-2 pt-2">
              <button type="button" @click="showSupplierModal = false" class="flex-1 py-2 border border-slate-700 rounded-xl text-slate-300">Отмена</button>
              <button type="submit" :disabled="creatingSupplier" class="flex-1 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold flex items-center justify-center gap-2">
                <span v-if="creatingSupplier" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>Создать в iiko</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const auth = useAuthStore()
const toast = useToastStore()

const invoice = ref(null)
const images = ref([])
const items = ref([])
const stores = ref([])
const suppliers = ref([])

const currentImageIndex = ref(0)
const zoomLevel = ref(1.0)
const reprocessing = ref(false)
const sendingToIiko = ref(false)

const currentImage = computed(() => images.value[currentImageIndex.value] || null)

const totalCalculatedSum = computed(() => {
  return items.value.reduce((acc, it) => acc + (parseFloat(it.iiko_sum) || 0), 0)
})

const hasUnmatchedItems = computed(() => {
  return items.value.some(it => !it.iiko_product_id)
})

function zoomIn() {
  if (zoomLevel.value < 2.5) zoomLevel.value = Math.round((zoomLevel.value + 0.25) * 100) / 100
}
function zoomOut() {
  if (zoomLevel.value > 0.5) zoomLevel.value = Math.round((zoomLevel.value - 0.25) * 100) / 100
}
function resetZoom() {
  zoomLevel.value = 1.0
}

async function loadInvoice() {
  try {
    const res = await api.get(`/invoices/documents/${route.params.id}/`, {
      params: { organization_id: auth.currentOrgId }
    })
    invoice.value = res.data
    images.value = res.data.images || []
    items.value = res.data.items || []

    // Автоподстановка поставщика в модалку если нужно
    if (res.data.raw_supplier_name) {
      newSupplierForm.value.name = res.data.raw_supplier_name
      newSupplierForm.value.inn = res.data.raw_supplier_inn || ''
    }
  } catch (e) {
    toast.error('Не удалось загрузить накладную')
  }
}

async function loadAuxData() {
  try {
    const [stRes, supRes] = await Promise.all([
      api.get('/invoices/stores/', { params: { organization_id: auth.currentOrgId } }),
      api.get('/invoices/suppliers/', { params: { organization_id: auth.currentOrgId } })
    ])
    stores.value = stRes.data || []
    suppliers.value = supRes.data || []
  } catch (e) {
    console.warn(e)
  }
}

async function saveHeader() {
  try {
    await api.patch(`/invoices/documents/${invoice.value.id}/update-header/`, {
      organization_id: auth.currentOrgId,
      invoice_number: invoice.value.invoice_number,
      invoice_date: invoice.value.invoice_date,
      iiko_supplier_id: invoice.value.iiko_supplier_id,
      iiko_store_id: invoice.value.iiko_store_id
    })
    toast.success('Параметры документа сохранены')
  } catch {
    toast.error('Не удалось сохранить параметры накладной')
  }
}

function onStoreChange() {
  const st = stores.value.find(s => String(s.id) === String(invoice.value.iiko_store_id))
  if (st) invoice.value.iiko_store_name = st.name
  saveHeader()
}

async function updateItemValues(item) {
  try {
    const res = await api.patch(`/invoices/documents/${invoice.value.id}/items/${item.id}/`, {
      organization_id: auth.currentOrgId,
      packaging_coefficient: item.packaging_coefficient,
      raw_amount: item.raw_amount,
      raw_price: item.raw_price,
      raw_sum: item.raw_sum,
      iiko_product_id: item.iiko_product_id,
      iiko_product_name: item.iiko_product_name
    })
    Object.assign(item, res.data)
  } catch {
    toast.error('Ошибка пересчета строки')
  }
}

// Live Search Catalog Modal
const searchModalOpen = ref(false)
const activeSearchItem = ref(null)
const catalogQuery = ref('')
const catalogResults = ref([])
let catalogSearchTimeout = null

function openSearchFor(item) {
  activeSearchItem.value = item
  catalogQuery.value = item.raw_name || ''
  searchModalOpen.value = true
  searchCatalog()
}

async function searchCatalog() {
  clearTimeout(catalogSearchTimeout)
  catalogSearchTimeout = setTimeout(async () => {
    try {
      const res = await api.get('/invoices/products-catalog/', {
        params: { organization_id: auth.currentOrgId, search: catalogQuery.value }
      })
      catalogResults.value = res.data || []
    } catch (e) {
      console.warn(e)
    }
  }, 250)
}

async function selectProductForActiveItem(prod) {
  if (!activeSearchItem.value) return
  activeSearchItem.value.iiko_product_id = prod.id
  activeSearchItem.value.iiko_product_name = prod.name
  activeSearchItem.value.iiko_product_code = prod.code
  activeSearchItem.value.match_status = 'green'
  await updateItemValues(activeSearchItem.value)
  searchModalOpen.value = false
  toast.success(`Сопоставлено: ${prod.name}`)
}

// Create Supplier Modal
const showSupplierModal = ref(false)
const creatingSupplier = ref(false)
const newSupplierForm = ref({ name: '', inn: '', code: '' })

async function createSupplierInIiko() {
  creatingSupplier.value = true
  try {
    const res = await api.post('/invoices/suppliers/', {
      organization_id: auth.currentOrgId,
      ...newSupplierForm.value
    })
    suppliers.value.unshift(res.data)
    invoice.value.iiko_supplier_id = res.data.id
    invoice.value.iiko_supplier_name = res.data.name
    await saveHeader()
    toast.success(`Поставщик '${res.data.name}' создан в iiko и привязан!`)
    showSupplierModal.value = false
  } catch (e) {
    const err = e.response?.data?.error || 'Ошибка при создании контрагента в iiko'
    toast.error(err)
  } finally {
    creatingSupplier.value = false
  }
}

async function reprocessInvoice() {
  reprocessing.value = true
  try {
    await api.post(`/invoices/documents/${invoice.value.id}/reprocess/`, {
      organization_id: auth.currentOrgId
    })
    toast.success('Накладная отправлена на повторное распознавание')
    setTimeout(loadInvoice, 3000)
  } catch {
    toast.error('Не удалось перезапустить распознавание')
  } finally {
    reprocessing.value = false
  }
}

async function sendToIiko() {
  sendingToIiko.value = true
  try {
    const res = await api.post(`/invoices/documents/${invoice.value.id}/send-to-iiko/`, {
      organization_id: auth.currentOrgId
    })
    toast.success(res.data.message || 'Приходная накладная создана в iiko!')
    await loadInvoice()
  } catch (e) {
    const err = e.response?.data?.error || 'Ошибка при выгрузке в iiko'
    toast.error(err)
  } finally {
    sendingToIiko.value = false
  }
}

function countByStatus(st) {
  return items.value.filter(it => it.match_status === st).length
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ru-RU')
}

function statusBadgeClass(st) {
  switch (st) {
    case 'sent_to_iiko':
      return 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
    case 'recognized':
      return 'bg-amber-950/60 text-amber-300 border-amber-800'
    case 'processing':
      return 'bg-indigo-950/60 text-indigo-300 border-indigo-800'
    case 'failed':
      return 'bg-rose-950/60 text-rose-300 border-rose-800'
    default:
      return 'bg-slate-800 text-slate-300 border-slate-700'
  }
}

onMounted(async () => {
  await Promise.all([loadInvoice(), loadAuxData()])
})
</script>
