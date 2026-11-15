<template>
  <div class="h-[calc(100vh-2rem)] flex flex-col p-6 space-y-4 overflow-hidden">
    <!-- Top Action Bar -->
    <div class="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-2xl px-6 py-4 flex-shrink-0">
      <div class="flex items-center gap-4">
        <button @click="$router.push('/admin/invoices')"
          class="w-9 h-9 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition-colors">
          ‹
        </button>
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-lg font-bold text-white">
              Накладная {{ invoice?.invoice_number ? `№ ${invoice.invoice_number}` : (invoice?.internal_number || '...') }}
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
            <span v-if="invoice?.author?.display" class="ml-2 px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-indigo-300">
              👤 {{ invoice.author.display }}
            </span>
            <span v-else-if="invoice?.uploaded_by_employee" class="ml-2 px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-indigo-300">
              📱 TMA: {{ invoice.uploaded_by_employee.first_name || 'Сотрудник' }}
            </span>
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-3">
        <button
          @click="reprocessInvoice"
          :disabled="reprocessing || invoice?.status === 'processing'"
          class="px-3.5 py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 disabled:opacity-50 cursor-pointer"
        >
          <span>↻</span>
          <span>{{ reprocessing ? 'Запуск...' : 'Перераспознать (AI)' }}</span>
        </button>

        <button
          v-if="invoice?.status !== 'sent_to_iiko'"
          @click="sendToIiko"
          :disabled="sendingToIiko || invoice?.status === 'processing' || hasUnmatchedItems"
          class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-2 cursor-pointer"
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

    <!-- DOCUMENT METADATA CARD (WITH MINI PHOTO THUMBNAIL) -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex-shrink-0 text-xs flex flex-col md:flex-row items-stretch md:items-center gap-4">
      <!-- Mini Photo Thumbnail Container -->
      <div 
        @click="openImageModal"
        title="Нажмите, чтобы открыть скан на весь экран"
        class="w-28 h-28 rounded-xl border border-slate-700 bg-slate-950 overflow-hidden relative group cursor-pointer flex-shrink-0 shadow-lg hover:border-indigo-500 transition-all flex items-center justify-center select-none"
      >
        <img 
          v-if="currentImage?.image_url" 
          :src="currentImage.image_url" 
          :alt="`Скан ${currentImageIndex + 1}`" 
          class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200" 
        />
        <div v-else class="text-slate-500 text-center p-2 text-[10px]">
          <span class="text-xl block mb-1">📄</span>
          Нет скана
        </div>

        <!-- Hover Overlay -->
        <div class="absolute inset-0 bg-indigo-950/70 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white gap-1 p-1 text-center">
          <span class="text-lg">🔍</span>
          <span class="text-[10px] font-bold leading-tight">Смотреть скан</span>
        </div>

        <!-- Pages badge -->
        <div v-if="images.length > 0" class="absolute bottom-1 right-1 bg-black/80 backdrop-blur-xs text-white text-[9px] font-mono font-bold px-1.5 py-0.5 rounded">
          {{ images.length }} стр.
        </div>
      </div>

      <!-- Metadata Fields: 2 Columns Layout -->
      <div class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3">
        <!-- Left Column: Дата накладной, затем Номер накладной -->
        <div class="flex flex-col gap-2.5">
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Дата накладной</label>
            <input v-model="invoice.invoice_date" @blur="saveHeader" type="date" class="form-input text-xs py-1.5 w-full" />
          </div>
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Номер накладной</label>
            <input v-model="invoice.invoice_number" @blur="saveHeader" type="text" class="form-input text-xs py-1.5 w-full" placeholder="Номер..." />
          </div>
        </div>

        <!-- Right Column: Поставщик в iiko, затем Склад оприходования -->
        <div class="flex flex-col gap-2.5">
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Поставщик в iiko</label>
            <div class="flex gap-1.5">
              <select v-model="invoice.iiko_supplier_id" @change="saveHeader" class="form-input text-xs py-1.5 flex-1">
                <option :value="null">-- Не выбран --</option>
                <option v-for="sup in suppliers" :key="sup.id" :value="sup.id">{{ sup.name }}</option>
              </select>
              <button @click="showSupplierModal = true" title="Создать контрагента в iiko"
                class="px-2.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 rounded-lg text-xs font-bold cursor-pointer transition-colors">
                +
              </button>
            </div>
          </div>
          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Склад оприходования</label>
            <select v-model="invoice.iiko_store_id" @change="onStoreChange" class="form-input text-xs py-1.5 w-full">
              <option :value="null">-- Не выбран --</option>
              <option v-for="st in stores" :key="st.id" :value="st.id">{{ st.name }}</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Quick Action: Open Scan Button -->
      <div class="flex flex-col justify-center border-t md:border-t-0 md:border-l border-slate-800 pt-2 md:pt-0 md:pl-4 flex-shrink-0">
        <button 
          @click="openImageModal"
          class="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 flex items-center justify-center gap-2 text-xs font-semibold cursor-pointer active:scale-95 transition-all"
        >
          <span>🔍</span>
          <span>Скан накладной ({{ images.length }} стр.)</span>
        </button>
      </div>
    </div>

    <!-- FULL WIDTH ITEMS TABLE CONTAINER -->
    <div class="flex-1 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col overflow-hidden shadow-xl min-h-0">
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
            <span class="text-white font-bold text-sm">{{ totalCalculatedSum.toLocaleString('ru-RU', { minimumFractionDigits: 2 }) }} ₸</span>
          </div>
        </div>
      </div>

      <!-- Scrollable Table -->
      <div class="flex-1 overflow-auto">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="sticky top-0 bg-slate-900 border-b border-slate-800 text-[11px] text-slate-400 uppercase tracking-wider z-10">
            <tr>
              <th class="px-3 py-2.5 w-10 text-center">#</th>
              <th class="px-4 py-2.5 min-w-[220px]">Из накладной (Фото)</th>
              <th class="px-4 py-2.5 min-w-[280px]">Товар в iiko (Номенклатура)</th>
              <th class="px-3 py-2.5 text-right w-24">Кол-во</th>
              <th class="px-4 py-2.5 text-center w-36">Фасовка (коэфф.)</th>
              <th class="px-3 py-2.5 text-right w-28">В iiko (баз.)</th>
              <th class="px-3 py-2.5 text-right w-28">Цена iiko</th>
              <th class="px-4 py-2.5 text-right w-32">Сумма в iiko</th>
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
              <td class="px-3 py-2 text-slate-500 font-mono text-[11px] text-center">{{ item.num }}</td>
              
              <!-- Raw name from invoice -->
              <td class="px-4 py-2">
                <p class="font-medium text-white text-xs leading-snug">{{ item.raw_name }}</p>
                <p class="text-[10px] text-slate-500 mt-0.5">
                  {{ item.raw_amount }} {{ item.raw_unit }} • по {{ item.raw_price }} ₸
                </p>
              </td>

              <!-- iiko Product selection -->
              <td class="px-4 py-2">
                <div class="flex items-center gap-2">
                  <span class="text-sm flex-shrink-0" :title="item.match_status === 'green' ? 'Точное совпадение' : item.match_status === 'yellow' ? 'Похожий товар' : 'Не найден в базе'">
                    {{ item.match_status === 'green' ? '🟢' : item.match_status === 'yellow' ? '🟡' : '🔴' }}
                  </span>
                  <div class="flex-1 relative">
                    <input
                      type="text"
                      :value="item.iiko_product_name"
                      @focus="openSearchFor(item)"
                      readonly
                      placeholder="Выберите товар iiko..."
                      class="form-input text-xs py-1.5 px-2.5 cursor-pointer w-full"
                      :class="item.iiko_product_id ? 'text-slate-100 font-medium' : 'text-rose-400 border-rose-800/80'"
                    />
                  </div>
                </div>
              </td>

              <!-- Raw Amount -->
              <td class="px-3 py-2 text-right font-mono font-medium text-slate-200">
                {{ item.raw_amount }} {{ item.raw_unit }}
              </td>

              <!-- Packaging Coefficient Adjuster -->
              <td class="px-4 py-2 text-center">
                <div class="inline-flex items-center gap-1.5">
                  <input
                    v-model.number="item.packaging_coefficient"
                    @change="updateItemValues(item)"
                    type="number"
                    step="0.001"
                    min="0.001"
                    class="form-input text-xs py-1 px-1.5 w-18 text-center font-mono font-bold"
                  />
                  <div class="flex flex-col gap-0.5">
                    <button @click="setPackFactor(item, 1.0)" class="text-[9px] px-1 py-0.2 rounded bg-slate-800 hover:bg-slate-700 text-slate-400">×1</button>
                    <button @click="setPackFactor(item, 2.0)" class="text-[9px] px-1 py-0.2 rounded bg-slate-800 hover:bg-slate-700 text-slate-400">×2</button>
                  </div>
                </div>
              </td>

              <!-- Computed Base Amount in iiko -->
              <td class="px-3 py-2 text-right font-mono text-xs">
                <span class="font-bold text-white">{{ item.iiko_amount }}</span>
              </td>

              <!-- Computed Price per Base Unit -->
              <td class="px-3 py-2 text-right font-mono text-xs text-slate-300">
                {{ item.iiko_price }} ₸
              </td>

              <!-- Computed Sum in iiko -->
              <td class="px-4 py-2 text-right font-mono text-xs">
                <span class="font-bold text-emerald-400">{{ Number(item.iiko_sum).toLocaleString('ru-RU', { minimumFractionDigits: 2 }) }} ₸</span>
                <span v-if="Number(item.sum_diff) !== 0" class="block text-[10px] text-amber-400/80" title="Погрешность копеек (компенсирована)">
                  Δ {{ item.sum_diff }} ₸
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- PHOTO VIEWER MODAL WITH ZOOM & PAGE CONTROLS -->
    <Transition name="fade">
      <div 
        v-if="showImageModal" 
        class="fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4 sm:p-6"
        @click.self="closeImageModal"
      >
        <div class="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden shadow-2xl">
          <!-- Modal Toolbar -->
          <div class="px-6 py-3.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between text-xs text-slate-300 flex-shrink-0">
            <!-- Left: Page Navigator -->
            <div class="flex items-center gap-3">
              <span class="font-bold text-white">
                📄 Страница {{ currentImageIndex + 1 }} из {{ images.length }}
              </span>

              <div class="flex items-center gap-1.5 ml-2">
                <button 
                  @click="prevPage" 
                  :disabled="currentImageIndex <= 0"
                  class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 font-bold"
                >
                  ‹ Назад
                </button>
                <button
                  v-for="(_, idx) in images"
                  :key="idx"
                  @click="currentImageIndex = idx"
                  class="w-6 h-6 rounded flex items-center justify-center font-mono text-[11px] transition-colors"
                  :class="currentImageIndex === idx ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 hover:bg-slate-700 text-slate-400'"
                >
                  {{ idx + 1 }}
                </button>
                <button 
                  @click="nextPage" 
                  :disabled="currentImageIndex >= images.length - 1"
                  class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 font-bold"
                >
                  Вперед ›
                </button>
              </div>
            </div>

            <!-- Right: Zoom, Rotate & Close -->
            <div class="flex items-center gap-2">
              <!-- Zoom Controls -->
              <div class="flex items-center bg-slate-800 rounded-xl p-0.5 border border-slate-700">
                <button @click="zoomOut" class="w-7 h-7 rounded-lg hover:bg-slate-700 text-white flex items-center justify-center font-bold text-sm">-</button>
                <span class="font-mono text-xs w-12 text-center text-slate-300">{{ Math.round(zoomLevel * 100) }}%</span>
                <button @click="zoomIn" class="w-7 h-7 rounded-lg hover:bg-slate-700 text-white flex items-center justify-center font-bold text-sm">+</button>
              </div>

              <!-- Reset Zoom -->
              <button @click="resetZoom" class="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium">
                100%
              </button>

              <!-- Rotate -->
              <button @click="rotateImage" title="Повернуть на 90°" class="px-2.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1">
                <span>⟳</span>
                <span>90°</span>
              </button>

              <!-- Close Button -->
              <button 
                @click="closeImageModal" 
                class="w-8 h-8 rounded-xl bg-slate-800 hover:bg-rose-600 hover:text-white border border-slate-700 text-slate-400 flex items-center justify-center font-bold text-sm transition-colors cursor-pointer ml-2"
                title="Закрыть (Esc)"
              >
                ✕
              </button>
            </div>
          </div>

          <!-- Modal Image Canvas (Pan & Zoom) -->
          <div class="flex-1 overflow-auto p-6 flex items-center justify-center bg-slate-950/90 relative select-none">
            <div 
              v-if="currentImage?.image_url" 
              class="transition-transform duration-150 origin-center flex items-center justify-center" 
              :style="{ 
                transform: `scale(${zoomLevel}) rotate(${rotationDegree}deg)`,
                transformOrigin: 'center center'
              }"
            >
              <img 
                :src="currentImage.image_url" 
                :alt="`Скан ${currentImageIndex + 1}`" 
                class="max-w-full max-h-[75vh] object-contain rounded-lg shadow-2xl border border-slate-800" 
              />
            </div>
            <div v-else class="text-slate-500 text-xs">Нет изображений для предпросмотра</div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Live Search Catalog Modal -->
    <Transition name="fade">
      <div v-if="searchModalOpen" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="searchModalOpen = false">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
          <div class="flex items-center justify-between pb-2 border-b border-slate-800">
            <h3 class="text-sm font-bold text-white">Выбор номенклатуры iiko</h3>
            <button @click="searchModalOpen = false" class="text-slate-400 hover:text-white">✕</button>
          </div>

          <div>
            <p class="text-[11px] text-slate-400 mb-1">Строка из накладной:</p>
            <p class="text-xs font-bold text-indigo-300 bg-slate-950/50 p-2 rounded border border-slate-800">
              {{ activeSearchItem?.raw_name }}
            </p>
          </div>

          <div>
            <input
              v-model="catalogQuery"
              @input="searchCatalog"
              type="text"
              class="form-input text-xs"
              placeholder="Поиск по названию или коду iiko..."
              autofocus
            />
          </div>

          <!-- Results List -->
          <div class="max-h-60 overflow-y-auto divide-y divide-slate-800 border border-slate-800 rounded-xl bg-slate-950/40">
            <div
              v-for="prod in catalogResults"
              :key="prod.id"
              @click="selectProductForActiveItem(prod)"
              class="p-2.5 hover:bg-indigo-600/20 cursor-pointer flex items-center justify-between transition-colors text-xs"
            >
              <div>
                <p class="font-medium text-white">{{ prod.name }}</p>
                <p class="text-[10px] text-slate-500 font-mono">{{ prod.code ? `Арт: ${prod.code}` : '' }} • Ед: {{ prod.unit || 'кг' }}</p>
              </div>
              <span class="text-xs text-indigo-400">Выбрать ➔</span>
            </div>
            <div v-if="!catalogResults.length" class="p-4 text-center text-xs text-slate-500">
              Товары не найдены
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Create Supplier Modal -->
    <Transition name="fade">
      <div v-if="showSupplierModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="showSupplierModal = false">
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
const rotationDegree = ref(0)
const showImageModal = ref(false)

const reprocessing = ref(false)
const sendingToIiko = ref(false)

const currentImage = computed(() => images.value[currentImageIndex.value] || null)

const totalCalculatedSum = computed(() => {
  return items.value.reduce((acc, it) => acc + (parseFloat(it.iiko_sum) || 0), 0)
})

const hasUnmatchedItems = computed(() => {
  return items.value.some(it => !it.iiko_product_id)
})

function openImageModal() {
  showImageModal.value = true
}

function closeImageModal() {
  showImageModal.value = false
}

function prevPage() {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
  }
}

function nextPage() {
  if (currentImageIndex.value < images.value.length - 1) {
    currentImageIndex.value++
  }
}

function zoomIn() {
  if (zoomLevel.value < 3.0) zoomLevel.value = Math.round((zoomLevel.value + 0.25) * 100) / 100
}

function zoomOut() {
  if (zoomLevel.value > 0.5) zoomLevel.value = Math.round((zoomLevel.value - 0.25) * 100) / 100
}

function resetZoom() {
  zoomLevel.value = 1.0
  rotationDegree.value = 0
}

function rotateImage() {
  rotationDegree.value = (rotationDegree.value + 90) % 360
}

function handleKeyDown(e) {
  if (e.key === 'Escape' && showImageModal.value) {
    closeImageModal()
  }
}

async function loadInvoice() {
  try {
    const res = await api.get(`/invoices/documents/${route.params.id}/`, {
      params: { organization_id: auth.currentOrgId }
    })
    invoice.value = res.data
    images.value = res.data.images || []
    items.value = res.data.items || []

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

function setPackFactor(item, factor) {
  item.packaging_coefficient = factor
  updateItemValues(item)
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
  window.addEventListener('keydown', handleKeyDown)
  await Promise.all([loadInvoice(), loadAuxData()])
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>
