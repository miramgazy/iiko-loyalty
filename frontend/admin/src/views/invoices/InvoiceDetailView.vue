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
          <div v-if="invoice?.sent_to_iiko_at" class="mt-1 text-[11px] text-emerald-400/90 flex flex-wrap items-center gap-x-2 gap-y-0.5 font-medium">
            <span>✅ Выгружено в iiko:</span>
            <span class="font-mono font-bold text-white">№ {{ invoice.iiko_document_number }}</span>
            <span>• Склад: <strong class="text-white">{{ invoice.iiko_store_name || 'выбранный склад' }}</strong></span>
            <span>• Учетная дата в iiko: <strong class="text-white">{{ formatDate(invoice.invoice_date) || 'текущая' }}</strong></span>
            <span class="text-slate-400">(Черновик / Непроведенная)</span>
          </div>
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
        <button
          v-else
          @click="sendToIiko"
          :disabled="sendingToIiko || invoice?.status === 'processing' || hasUnmatchedItems"
          class="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-emerald-400 border border-emerald-800/60 rounded-xl text-xs font-semibold transition-all flex items-center gap-2 cursor-pointer"
          title="Обновить или повторно отправить накладную в iiko"
        >
          <span v-if="sendingToIiko" class="w-3.5 h-3.5 border-2 border-emerald-400/30 border-t-emerald-400 rounded-full animate-spin"></span>
          <span>🔄 Обновить в iiko</span>
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
            <label class="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5 mb-1">
              <span class="text-indigo-400">📅</span>
              Дата накладной
            </label>
            <input 
              v-model="invoice.invoice_date" 
              @blur="saveHeader" 
              type="date" 
              class="form-input text-xs py-2 px-3 w-full bg-slate-950/90 border border-slate-700/90 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white font-mono shadow-inner [color-scheme:dark] transition-all" 
            />
          </div>
          <div>
            <label class="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5 mb-1">
              <span class="text-indigo-400">🔢</span>
              Номер накладной
            </label>
            <input 
              v-model="invoice.invoice_number" 
              @blur="saveHeader" 
              type="text" 
              class="form-input text-xs py-2 px-3 w-full bg-slate-950/90 border border-slate-700/90 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white font-mono shadow-inner transition-all placeholder:text-slate-500" 
              placeholder="Номер накладной..." 
            />
          </div>
        </div>

        <!-- Right Column: Поставщик в iiko, затем Склад оприходования -->
        <div class="flex flex-col gap-2.5">
          <div>
            <label class="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5 mb-1">
              <span class="text-indigo-400">🏢</span>
              Поставщик в iiko
            </label>
            <div class="flex items-center gap-2">
              <select 
                v-model="invoice.iiko_supplier_id" 
                @change="saveHeader" 
                class="form-input text-xs py-2 px-3 flex-1 bg-slate-950/90 border border-slate-700/90 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white shadow-inner transition-all truncate"
              >
                <option :value="null">-- Не выбран --</option>
                <option v-for="sup in suppliers" :key="sup.id" :value="sup.id">{{ sup.name }}</option>
              </select>
              <button 
                @click="openSupplierModal" 
                type="button"
                title="Создать нового контрагента в iiko"
                class="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 active:scale-95 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/30 border border-indigo-400/40 cursor-pointer transition-all flex-shrink-0"
              >
                <span class="text-base font-extrabold leading-none">+</span>
                <span class="font-semibold text-xs">Новый</span>
              </button>
            </div>
          </div>
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <span class="text-indigo-400">🏬</span>
                Склад оприходования
              </label>
              <label class="inline-flex items-center gap-1.5 cursor-pointer text-[11px] text-indigo-300 hover:text-white select-none">
                <input 
                  type="checkbox" 
                  v-model="invoice.has_different_stores" 
                  @change="onDifferentStoresToggle"
                  class="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-indigo-500/30 w-3.5 h-3.5 cursor-pointer"
                />
                <span class="font-medium">Разные склады</span>
              </label>
            </div>
            <select 
              v-model="invoice.iiko_store_id" 
              @change="onStoreChange" 
              class="form-input text-xs py-2 px-3 w-full bg-slate-950/90 border border-slate-700/90 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white shadow-inner transition-all truncate"
            >
              <option :value="null">-- Не выбран --</option>
              <option v-for="st in stores" :key="st.id" :value="st.id">{{ st.name }}</option>
            </select>
            <p v-if="invoice?.has_different_stores" class="text-[10px] text-indigo-400/90 mt-1">
              ℹ️ В таблице ниже можно указать свой склад для каждой позиции (по умолчанию подставляется выбранный выше).
            </p>
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
              <th v-if="invoice?.has_different_stores" class="px-3 py-2.5 min-w-[180px]">Склад</th>
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
                <p v-if="item.clean_name && item.clean_name !== item.raw_name" class="text-[10px] text-indigo-300 font-medium mt-0.5 flex items-center gap-1">
                  <span>✨ Поиск:</span> {{ item.clean_name }}
                </p>
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

                <!-- Quick Candidate Suggestions Pills -->
                <div v-if="item.candidates && item.candidates.length > 0 && item.match_status !== 'green'" class="flex flex-wrap items-center gap-1.5 mt-1.5 pl-6">
                  <span class="text-[10px] text-slate-400">💡 Похожие:</span>
                  <button
                    v-for="cand in item.candidates.slice(0, 3)"
                    :key="cand.id"
                    type="button"
                    @click.stop="quickSelectCandidate(item, cand)"
                    class="px-2 py-0.5 rounded-lg bg-indigo-950/70 hover:bg-indigo-600 hover:text-white text-indigo-300 border border-indigo-800/80 text-[10px] font-medium transition-colors cursor-pointer flex items-center gap-1"
                    :title="`Выбрать: ${cand.name} (${Math.round(cand.score * 100)}% совпадение)`"
                  >
                    <span>{{ cand.name }}</span>
                    <span class="opacity-75 font-mono text-[9px]">{{ Math.round(cand.score * 100) }}%</span>
                  </button>
                </div>
              </td>

              <!-- Store per item (when different stores is enabled) -->
              <td v-if="invoice?.has_different_stores" class="px-3 py-2">
                <select 
                  v-model="item.iiko_store_id"
                  @change="onItemStoreChange(item)"
                  class="form-input text-xs py-1.5 px-2.5 w-full bg-slate-950/90 border border-slate-700/80 hover:border-slate-500 focus:border-indigo-500 rounded-xl text-white truncate transition-all"
                >
                  <option :value="null">-- По умолчанию --</option>
                  <option v-for="st in stores" :key="st.id" :value="st.id">{{ st.name }}</option>
                </select>
              </td>

              <!-- Raw Amount -->
              <td class="px-3 py-2 text-right font-mono font-medium text-slate-200">
                {{ item.raw_amount }} {{ item.raw_unit }}
              </td>

              <!-- Packaging Coefficient Adjuster -->
              <td class="px-4 py-2 text-center">
                <div class="inline-flex items-center justify-center gap-1.5">
                  <input
                    v-model.number="item.packaging_coefficient"
                    @change="updateItemValues(item)"
                    type="number"
                    step="0.001"
                    min="0.001"
                    title="Коэффициент фасовки (базовых единиц в 1 ед. накладной)"
                    class="form-input text-xs py-1 px-1.5 w-18 text-center font-mono font-bold bg-slate-900 border-slate-700 focus:border-indigo-500 rounded"
                  />
                  <button
                    type="button"
                    @click="openPackagingModal(item)"
                    class="p-1 rounded-lg bg-indigo-950/70 hover:bg-indigo-600 text-indigo-300 hover:text-white border border-indigo-800/80 transition-colors shadow-xs"
                    title="Калькулятор единиц и фасовки (штуки, вес, тара)"
                  >
                    ⚖️
                  </button>
                </div>
                <div v-if="item.iiko_container_name" class="text-[9px] text-indigo-400 truncate max-w-[130px] mx-auto mt-0.5" :title="item.iiko_container_name">
                  📦 {{ item.iiko_container_name }}
                </div>
              </td>

              <!-- Computed Base Amount in iiko (Editable for direct piece entry) -->
              <td class="px-3 py-2 text-right">
                <div class="inline-flex items-center justify-end gap-1">
                  <input
                    v-model.number="item.iiko_amount"
                    @change="onIikoAmountChange(item)"
                    type="number"
                    step="0.001"
                    min="0.001"
                    title="Количество в базовых единицах iiko (измените число для пересчета штучности)"
                    class="form-input text-xs py-1 px-1.5 w-20 text-right font-mono font-bold bg-slate-900 border-slate-700 focus:border-indigo-500 rounded text-white"
                  />
                  <span class="text-[10px] text-slate-400 font-mono flex-shrink-0" :title="`Единица в iiko: ${formatUnitName(item.iiko_product_unit || item.raw_unit)}`">
                    {{ formatUnitName(item.iiko_product_unit || item.raw_unit || 'кг') }}
                  </span>
                </div>
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
            <div class="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800 space-y-1">
              <p class="text-xs font-bold text-white">{{ activeSearchItem?.raw_name }}</p>
              <p v-if="activeSearchItem?.clean_name && activeSearchItem.clean_name !== activeSearchItem.raw_name" class="text-[11px] text-indigo-400 font-medium flex items-center gap-1">
                <span>✨ Смысловое ядро (AI):</span> {{ activeSearchItem.clean_name }}
              </p>
            </div>

            <!-- Блок исправления неточного распознавания текста -->
            <div class="mt-2.5 space-y-2">
              <div class="flex items-center justify-between">
                <label class="inline-flex items-center gap-2 cursor-pointer text-xs font-medium text-amber-300 hover:text-amber-200 select-none">
                  <input 
                    type="checkbox" 
                    v-model="isImpreciseRecognition" 
                    @change="onImpreciseToggle"
                    class="rounded border-amber-800 bg-slate-950 text-amber-500 focus:ring-amber-500/30 w-3.5 h-3.5 cursor-pointer"
                  />
                  <span>⚠️ Неточное распознавание текста (исправить вручную)</span>
                </label>
              </div>

              <!-- Поле редактирования при активной галочке -->
              <div v-if="isImpreciseRecognition" class="p-3 rounded-xl bg-amber-950/25 border border-amber-800/50 space-y-2">
                <div>
                  <label class="text-[11px] font-semibold text-amber-200 block mb-1">
                    Исправленное название товара:
                  </label>
                  <div class="flex items-center gap-2">
                    <input 
                      v-model="editedRawName"
                      @keyup.enter="applyEditedText"
                      type="text" 
                      class="form-input text-xs py-1.5 px-3 flex-1 bg-slate-950/90 border border-amber-700/80 hover:border-amber-500 focus:border-amber-400 focus:ring-2 focus:ring-amber-400/25 rounded-xl text-white font-medium shadow-inner"
                      placeholder="Введите правильное название из накладной..."
                    />
                    <button 
                      type="button" 
                      @click="applyEditedText"
                      class="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 active:scale-95 text-white font-bold rounded-xl text-xs transition-all shadow-md shadow-amber-600/20 whitespace-nowrap cursor-pointer flex items-center gap-1 flex-shrink-0"
                      title="Применить текст и найти в каталоге iiko"
                    >
                      <span>🔍</span>
                      <span>Искать в iiko</span>
                    </button>
                  </div>
                  <p class="text-[10px] text-slate-400 mt-1">
                    Название в строке обновится, а каталог iiko сразу выдаст подходящие товары.
                  </p>
                </div>

                <div class="pt-1.5 border-t border-amber-900/40">
                  <label class="inline-flex items-center gap-2 cursor-pointer text-[11px] text-slate-300 hover:text-white select-none">
                    <input 
                      type="checkbox" 
                      v-model="skipKnowledgeBase" 
                      class="rounded border-slate-700 bg-slate-950 text-indigo-500 focus:ring-indigo-500/30 w-3.5 h-3.5 cursor-pointer"
                    />
                    <span>Не сохранять в базу знаний (разовое сопоставление)</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <!-- Suggested candidates if present -->
          <div v-if="activeSearchItem?.candidates && activeSearchItem.candidates.length > 0" class="space-y-1.5">
            <p class="text-[11px] font-semibold text-slate-300 flex items-center gap-1">
              <span>💡</span> Рекомендованные совпадения (AI):
            </p>
            <div class="flex flex-col gap-1.5 max-h-36 overflow-y-auto">
              <div
                v-for="cand in activeSearchItem.candidates"
                :key="cand.id"
                @click="selectProductForActiveItem(cand)"
                class="p-2 rounded-xl bg-indigo-950/40 hover:bg-indigo-600/30 border border-indigo-800/60 cursor-pointer flex items-center justify-between transition-colors text-xs"
              >
                <div>
                  <p class="font-medium text-white">{{ cand.name }}</p>
                  <p class="text-[10px] text-slate-400 font-mono">{{ cand.code ? `Арт: ${cand.code}` : '' }} • Ед: {{ formatUnitName(cand.unit || 'кг') }}</p>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-[10px] font-bold font-mono px-1.5 py-0.5 rounded bg-indigo-900/60 text-indigo-300">
                    {{ Math.round(cand.score * 100) }}%
                  </span>
                  <span class="text-xs text-indigo-400 font-bold">Выбрать ➔</span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <label class="text-[11px] font-semibold text-slate-400 block mb-1">Поиск по каталогу iiko:</label>
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
                <p class="text-[10px] text-slate-500 font-mono">{{ prod.code ? `Арт: ${prod.code}` : '' }} • Ед: {{ formatUnitName(prod.unit || 'кг') }}</p>
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

    <!-- Packaging & Unit Conversion Modal -->
    <Transition name="fade">
      <div 
        v-if="packagingModalOpen && activePackItem" 
        class="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4 sm:p-6" 
        @click.self="packagingModalOpen = false"
      >
        <div class="bg-slate-900 border border-slate-700/80 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
          <!-- Modal Header -->
          <div class="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-lg flex-shrink-0 shadow-inner">
                ⚖️
              </div>
              <div>
                <h3 class="text-sm font-bold text-white">Пересчет единиц измерения и фасовки</h3>
                <p class="text-[11px] text-slate-400 mt-0.5">Пересчет между накладной поставщика и складом iiko</p>
              </div>
            </div>
            <button 
              type="button"
              @click="packagingModalOpen = false" 
              class="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            >
              ✕
            </button>
          </div>

          <div class="p-6 space-y-5 overflow-y-auto max-h-[80vh]">
            <!-- Item Info Banner -->
            <div class="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800/80 space-y-2">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <span class="text-[10px] text-slate-500 font-mono uppercase tracking-wider block">Из накладной:</span>
                  <p class="text-xs font-semibold text-white">{{ activePackItem.raw_name }}</p>
                </div>
                <div class="text-right flex-shrink-0">
                  <span class="text-xs font-mono font-bold text-slate-200">
                    {{ activePackItem.raw_amount }} {{ activePackItem.raw_unit }}
                  </span>
                  <span class="text-[11px] text-slate-400 font-mono block">
                    {{ Number(activePackItem.raw_sum).toLocaleString('ru-RU') }} ₸
                  </span>
                </div>
              </div>
              <div class="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-2">
                <div>
                  <span class="text-[10px] text-indigo-400 font-mono uppercase tracking-wider block">Товар в iiko:</span>
                  <p class="text-xs font-semibold text-indigo-200">{{ activePackItem.iiko_product_name || 'Не сопоставлен' }}</p>
                </div>
                <div class="flex items-center gap-1.5">
                  <span class="text-[11px] text-slate-400">Ед. в iiko:</span>
                  <input
                    v-model="packItemUnit"
                    placeholder="шт, кг..."
                    class="form-input text-xs py-0.5 px-2 w-16 text-center font-bold bg-slate-900 border-slate-700 text-white rounded"
                  />
                </div>
              </div>
            </div>

            <!-- Conversion Mode Selector Tabs -->
            <div>
              <label class="text-[11px] font-semibold text-slate-300 block mb-2">Способ пересчета:</label>
              <div class="grid grid-cols-3 gap-1.5 p-1 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-medium text-slate-400">
                <button
                  type="button"
                  @click="packMode = 'direct'"
                  class="py-1.5 px-2 rounded-lg transition-all text-center cursor-pointer"
                  :class="packMode === 'direct' ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'hover:text-slate-200'"
                >
                  🔢 В штуках
                </button>
                <button
                  type="button"
                  @click="packMode = 'piece_weight'"
                  class="py-1.5 px-2 rounded-lg transition-all text-center cursor-pointer"
                  :class="packMode === 'piece_weight' ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'hover:text-slate-200'"
                >
                  ⚖️ По весу 1 шт.
                </button>
                <button
                  type="button"
                  @click="packMode = 'coefficient'"
                  class="py-1.5 px-2 rounded-lg transition-all text-center cursor-pointer"
                  :class="packMode === 'coefficient' ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'hover:text-slate-200'"
                >
                  ✖️ Коэффициент
                </button>
              </div>
            </div>

            <!-- Mode 1: Direct Piece / Base Amount Entry -->
            <div v-if="packMode === 'direct'" class="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-800/40 space-y-3">
              <label class="text-xs font-semibold text-indigo-200 block">
                Сколько штук (или {{ packItemUnit || 'базовых единиц' }}) оприходовать в iiko:
              </label>
              <div class="flex items-center gap-3">
                <input
                  v-model.number="directAmount"
                  type="number"
                  step="0.001"
                  min="0.001"
                  placeholder="Например, 6"
                  class="form-input text-sm py-2 px-3 w-36 font-mono font-bold text-white bg-slate-950 border-slate-700 focus:border-indigo-500 rounded-xl text-center"
                />
                <span class="text-xs text-slate-300 font-semibold">{{ packItemUnit || 'шт' }}</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                💡 Например: в накладной указано {{ activePackItem.raw_amount }} {{ activePackItem.raw_unit }} рыбы, а фактически это {{ directAmount || '?' }} штук.
              </p>
            </div>

            <!-- Mode 2: By Piece Weight -->
            <div v-if="packMode === 'piece_weight'" class="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-800/40 space-y-3">
              <label class="text-xs font-semibold text-indigo-200 block">
                Средний вес одной рыбы / штуки (в {{ activePackItem.raw_unit || 'кг' }}):
              </label>
              <div class="flex items-center gap-3">
                <input
                  v-model.number="pieceWeight"
                  type="number"
                  step="0.001"
                  min="0.001"
                  placeholder="Например, 2.5"
                  class="form-input text-sm py-2 px-3 w-36 font-mono font-bold text-white bg-slate-950 border-slate-700 focus:border-indigo-500 rounded-xl text-center"
                />
                <span class="text-xs text-slate-300 font-semibold">{{ activePackItem.raw_unit || 'кг' }} / 1 {{ packItemUnit || 'шт' }}</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                💡 При общем весе {{ activePackItem.raw_amount }} {{ activePackItem.raw_unit }} и среднем весе {{ pieceWeight || '?' }} {{ activePackItem.raw_unit }}, получится 
                <strong class="text-emerald-400">{{ calculatedDirectAmount }} {{ packItemUnit || 'шт' }}</strong>.
              </p>
            </div>

            <!-- Mode 3: Direct Packaging Coefficient -->
            <div v-if="packMode === 'coefficient'" class="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-800/40 space-y-3">
              <label class="text-xs font-semibold text-indigo-200 block">
                Коэффициент фасовки (базовых единиц iiko в 1 единице накладной):
              </label>
              <div class="flex items-center gap-3">
                <input
                  v-model.number="customCoefficient"
                  type="number"
                  step="0.001"
                  min="0.001"
                  placeholder="1.000"
                  class="form-input text-sm py-2 px-3 w-36 font-mono font-bold text-white bg-slate-950 border-slate-700 focus:border-indigo-500 rounded-xl text-center"
                />
                <div class="flex items-center gap-1">
                  <button type="button" @click="customCoefficient = 1.0" class="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">×1</button>
                  <button type="button" @click="customCoefficient = 0.4" class="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">0.4</button>
                  <button type="button" @click="customCoefficient = 2.5" class="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">2.5</button>
                </div>
              </div>
            </div>

            <!-- Predefined iiko Containers (if available for this product) -->
            <div v-if="availableContainers && availableContainers.length > 0" class="space-y-2">
              <label class="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                <span>📦</span> Фасовки и тара из карточки товара iiko:
              </label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="c in availableContainers"
                  :key="c.id"
                  type="button"
                  @click="selectContainer(c)"
                  class="p-2.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between"
                  :class="selectedContainerId === c.id ? 'bg-indigo-600/30 border-indigo-500 text-white' : 'bg-slate-950/70 border-slate-800 hover:border-slate-700 text-slate-300'"
                >
                  <span class="text-xs font-semibold truncate">{{ c.name }}</span>
                  <span class="text-[10px] text-slate-400 font-mono mt-1">Коэфф: {{ c.count }}</span>
                </button>
              </div>
            </div>

            <!-- Live Calculation Preview -->
            <div class="p-4 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 space-y-2">
              <span class="text-[10px] text-emerald-400 font-mono uppercase tracking-wider block font-bold">Итог оприходования в iiko:</span>
              <div class="grid grid-cols-3 gap-2 pt-1 text-center font-mono">
                <div class="p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
                  <span class="text-[9px] text-slate-400 block">Количество</span>
                  <span class="text-xs font-bold text-emerald-300">{{ calculatedDirectAmount }} {{ packItemUnit || 'шт' }}</span>
                </div>
                <div class="p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
                  <span class="text-[9px] text-slate-400 block">Цена за 1 {{ packItemUnit || 'шт' }}</span>
                  <span class="text-xs font-bold text-white">{{ calculatedPrice }} ₸</span>
                </div>
                <div class="p-2 rounded-xl bg-slate-950/60 border border-slate-800/60">
                  <span class="text-[9px] text-slate-400 block">Сумма в iiko</span>
                  <span class="text-xs font-bold text-emerald-400">{{ Number(activePackItem.raw_sum).toLocaleString('ru-RU') }} ₸</span>
                </div>
              </div>
              <p class="text-[10px] text-slate-400 pt-1 text-center font-mono">
                Коэффициент фасовки: <strong>{{ calculatedCoeff }}</strong> • Баланс строки сохраняется точным до копейки
              </p>
            </div>

            <!-- Knowledge Base Checkbox -->
            <label class="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/70 border border-slate-800 cursor-pointer hover:bg-slate-950 transition-colors">
              <input
                v-model="savePackToKB"
                type="checkbox"
                class="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-indigo-500 mt-0.5"
              />
              <span class="text-xs text-slate-300 leading-snug">
                🧠 <strong>Запомнить фасовку в базе знаний</strong> для поставщика 
                <span class="text-indigo-300">«{{ invoice.iiko_supplier_name || invoice.raw_supplier_name }}»</span>
                (следующие накладные пересчитаются автоматически)
              </span>
            </label>
          </div>

          <!-- Modal Footer -->
          <div class="px-6 py-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              @click="packagingModalOpen = false"
              class="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            >
              Отмена
            </button>
            <button
              type="button"
              @click="applyPackagingModal"
              class="px-5 py-2 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-600/30 flex items-center gap-1.5 cursor-pointer"
            >
              <span>Применить пересчет</span>
              <span>✓</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Create Supplier Modal -->
    <Transition name="fade">
      <div 
        v-if="showSupplierModal" 
        class="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-4 sm:p-6" 
        @click.self="showSupplierModal = false"
      >
        <div class="bg-slate-900 border border-slate-700/80 rounded-3xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
          <!-- Modal Header -->
          <div class="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-lg flex-shrink-0 shadow-inner">
                🏢
              </div>
              <div>
                <h3 class="text-sm font-bold text-white">Создать контрагента в iiko</h3>
                <p class="text-[11px] text-slate-400 mt-0.5">Новый поставщик будет зарегистрирован в iiko Server и привязан к накладной</p>
              </div>
            </div>
            <button 
              type="button"
              @click="showSupplierModal = false" 
              class="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-750 text-slate-400 hover:text-white flex items-center justify-center transition-colors text-sm font-bold cursor-pointer"
            >
              ✕
            </button>
          </div>

          <!-- Modal Body / Form -->
          <form @submit.prevent="createSupplierInIiko" class="p-6 space-y-4">
            <!-- Supplier Name Field -->
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                <span class="flex items-center gap-1.5">
                  <span class="text-indigo-400">🏷️</span>
                  Наименование поставщика <span class="text-rose-400">*</span>
                </span>
                <span v-if="invoice?.raw_supplier_name && newSupplierForm.name === invoice.raw_supplier_name" class="text-[10px] font-normal text-indigo-400 flex items-center gap-1 bg-indigo-950/60 border border-indigo-800/60 px-2 py-0.5 rounded-full">
                  ✨ из накладной
                </span>
              </label>
              <input 
                v-model="newSupplierForm.name" 
                type="text" 
                class="form-input text-xs py-2.5 px-3.5 w-full bg-slate-950/90 border border-slate-700/80 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white placeholder-slate-500 shadow-inner outline-none transition-all" 
                placeholder="например: ТОО Фуд Дистрибьюшн" 
                required 
                autofocus
              />
            </div>

            <!-- 2-Columns: INN/BIN and Code -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <span class="text-indigo-400">🪪</span>
                  БИН / ИНН
                </label>
                <input 
                  v-model="newSupplierForm.inn" 
                  type="text" 
                  class="form-input text-xs py-2.5 px-3.5 w-full bg-slate-950/90 border border-slate-700/80 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white placeholder-slate-500 shadow-inner font-mono outline-none transition-all" 
                  placeholder="12 цифр..." 
                />
              </div>

              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <span class="text-indigo-400">🔖</span>
                  Артикул / Код
                </label>
                <input 
                  v-model="newSupplierForm.code" 
                  type="text" 
                  class="form-input text-xs py-2.5 px-3.5 w-full bg-slate-950/90 border border-slate-700/80 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white placeholder-slate-500 shadow-inner font-mono outline-none transition-all" 
                  placeholder="Код в iiko..." 
                />
              </div>
            </div>

            <!-- Phone field (optional) -->
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                <span class="text-indigo-400">📞</span>
                Номер телефона <span class="text-[10px] text-slate-500 font-normal">(опционально)</span>
              </label>
              <input 
                v-model="newSupplierForm.phone" 
                type="tel" 
                class="form-input text-xs py-2.5 px-3.5 w-full bg-slate-950/90 border border-slate-700/80 hover:border-slate-500 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/25 rounded-xl text-white placeholder-slate-500 shadow-inner font-mono outline-none transition-all" 
                placeholder="+7 (700) 000-00-00" 
              />
            </div>

            <!-- Modal Action Buttons -->
            <div class="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <button 
                type="button" 
                @click="showSupplierModal = false" 
                class="px-4 py-2.5 border border-slate-700 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              >
                Отмена
              </button>
              <button 
                type="submit" 
                :disabled="creatingSupplier || !newSupplierForm.name.trim()" 
                class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 cursor-pointer transition-all active:scale-95"
              >
                <span v-if="creatingSupplier" class="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>{{ creatingSupplier ? 'Создание...' : 'Создать в iiko' }}</span>
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
      iiko_store_id: invoice.value.iiko_store_id,
      has_different_stores: invoice.value.has_different_stores
    })
    toast.success('Параметры документа сохранены')
  } catch {
    toast.error('Не удалось сохранить параметры накладной')
  }
}

async function onStoreChange() {
  const st = stores.value.find(s => String(s.id) === String(invoice.value.iiko_store_id))
  if (st) invoice.value.iiko_store_name = st.name
  await saveHeader()
}

async function onDifferentStoresToggle() {
  if (invoice.value?.has_different_stores) {
    // If enabled, for any items without a store, pre-populate header store
    for (const it of items.value) {
      if (!it.iiko_store_id && invoice.value.iiko_store_id) {
        it.iiko_store_id = invoice.value.iiko_store_id
        it.iiko_store_name = invoice.value.iiko_store_name
        await updateItemValues(it)
      }
    }
  }
  await saveHeader()
}

// Справочник единиц измерения iiko (UUID -> Название)
const STANDARD_UNITS = {
  '7ba81c3a-8de5-8f9d-fb9f-e39efcbc57cc': 'кг',
  'cd19b5ea-1b32-a6e5-1df7-5d2784a0549a': 'шт',
  '6040d92d-e286-f4f9-a613-ed0e6fd241e1': 'порц',
  '69859c74-db72-b006-cba5-326cf6f4fc6e': 'л',
  'b003f902-de36-c128-019f-7e1d6ef2280b': 'услуга',
  'b003f902-de36-c128-019f-7e1d6ef228b2': 'м',
  'b003f902-de36-c128-019f-7e1d6ef22a4a': 'пара',
}

function formatUnitName(unit) {
  if (!unit) return 'кг'
  const str = String(unit).trim().toLowerCase()
  if (STANDARD_UNITS[str]) {
    return STANDARD_UNITS[str]
  }
  // Если значение является UUID (36 символов с 4 дефисами)
  if (str.length === 36 && str.split('-').length === 5) {
    return 'шт'
  }
  return unit
}

async function onItemStoreChange(item) {
  const st = stores.value.find(s => String(s.id) === String(item.iiko_store_id))
  item.iiko_store_name = st ? st.name : ''
  await updateItemValues(item)
  toast.success(`Склад позиции обновлен: ${item.iiko_store_name || 'По умолчанию'}`)
}

function setPackFactor(item, factor) {
  item.packaging_coefficient = factor
  updateItemValues(item)
}

async function onIikoAmountChange(item) {
  if (item.iiko_amount && Number(item.iiko_amount) > 0) {
    await updateItemValues(item, {
      target_iiko_amount: Number(item.iiko_amount),
      iiko_product_unit: item.iiko_product_unit
    })
    toast.success(`Пересчитано: ${item.iiko_amount} ${item.iiko_product_unit || ''} (коэфф. ${item.packaging_coefficient})`)
  }
}

async function updateItemValues(item, extra = {}) {
  try {
    const payload = {
      organization_id: auth.currentOrgId,
      raw_name: item.raw_name,
      clean_name: item.clean_name,
      packaging_coefficient: item.packaging_coefficient,
      raw_amount: item.raw_amount,
      raw_price: item.raw_price,
      raw_sum: item.raw_sum,
      iiko_product_id: item.iiko_product_id,
      iiko_product_name: item.iiko_product_name,
      iiko_product_code: item.iiko_product_code,
      iiko_product_unit: item.iiko_product_unit,
      iiko_container_id: item.iiko_container_id,
      iiko_container_name: item.iiko_container_name,
      iiko_store_id: item.iiko_store_id,
      iiko_store_name: item.iiko_store_name,
      is_imprecise_recognition: item.is_imprecise_recognition,
      skip_knowledge_base: item.skip_knowledge_base,
      ...extra
    }
    const res = await api.patch(`/invoices/documents/${invoice.value.id}/items/${item.id}/`, payload)
    Object.assign(item, res.data)
  } catch {
    toast.error('Ошибка пересчета строки')
  }
}

// Packaging & Unit Conversion Modal State & Logic
const packagingModalOpen = ref(false)
const activePackItem = ref(null)
const packMode = ref('direct')
const directAmount = ref(1)
const pieceWeight = ref(1)
const customCoefficient = ref(1)
const selectedContainerId = ref('')
const selectedContainerName = ref('')
const availableContainers = ref([])
const packItemUnit = ref('')
const savePackToKB = ref(true)

const calculatedDirectAmount = computed(() => {
  if (!activePackItem.value) return 0
  const rawAmt = Number(activePackItem.value.raw_amount) || 0
  if (packMode.value === 'direct') {
    return Number(directAmount.value) || 0
  }
  if (packMode.value === 'piece_weight') {
    const pw = Number(pieceWeight.value)
    if (pw > 0 && rawAmt > 0) {
      return Number((rawAmt / pw).toFixed(3))
    }
    return 0
  }
  if (packMode.value === 'coefficient') {
    const k = Number(customCoefficient.value) || 1.0
    return Number((rawAmt * k).toFixed(3))
  }
  return 0
})

const calculatedCoeff = computed(() => {
  if (!activePackItem.value) return 1.0
  const rawAmt = Number(activePackItem.value.raw_amount) || 0
  const directAmt = calculatedDirectAmount.value
  if (rawAmt > 0 && directAmt > 0) {
    return Number((directAmt / rawAmt).toFixed(3))
  }
  return 1.0
})

const calculatedPrice = computed(() => {
  if (!activePackItem.value) return '0.00'
  const rawSum = Number(activePackItem.value.raw_sum) || 0
  const directAmt = calculatedDirectAmount.value
  if (directAmt > 0) {
    return (rawSum / directAmt).toFixed(2)
  }
  return Number(activePackItem.value.raw_price || 0).toFixed(2)
})

async function openPackagingModal(item) {
  activePackItem.value = item
  packMode.value = 'direct'
  directAmount.value = Number(item.iiko_amount) || Number(item.raw_amount) || 1
  pieceWeight.value = Number(item.raw_amount) && Number(item.iiko_amount) ? Number((Number(item.raw_amount) / Number(item.iiko_amount)).toFixed(3)) : 1.0
  customCoefficient.value = Number(item.packaging_coefficient) || 1.0
  selectedContainerId.value = item.iiko_container_id || ''
  selectedContainerName.value = item.iiko_container_name || ''
  packItemUnit.value = formatUnitName(item.iiko_product_unit || (item.raw_unit === 'кг' ? 'шт' : item.raw_unit) || 'шт')
  savePackToKB.value = !item.skip_knowledge_base
  availableContainers.value = []

  // Пытаемся получить список фасовок товара из iiko
  if (item.iiko_product_id) {
    try {
      const res = await api.get('/invoices/products-catalog/', {
        params: { organization_id: auth.currentOrgId, search: item.iiko_product_name || '' }
      })
      const found = (res.data || []).find(p => String(p.id).toLowerCase() === String(item.iiko_product_id).toLowerCase())
      if (found) {
        if (found.unit && !item.iiko_product_unit) {
          packItemUnit.value = formatUnitName(found.unit)
        }
        if (found.containers && found.containers.length > 0) {
          availableContainers.value = found.containers
        }
      }
    } catch (e) {
      console.warn('Could not load containers:', e)
    }
  }

  packagingModalOpen.value = true
}

function selectContainer(c) {
  selectedContainerId.value = c.id
  selectedContainerName.value = c.name
  customCoefficient.value = Number(c.count) || 1.0
  packMode.value = 'coefficient'
}

async function applyPackagingModal() {
  if (!activePackItem.value) return
  const unit = packItemUnit.value.trim() || 'шт'
  const targetAmount = calculatedDirectAmount.value
  const coeff = calculatedCoeff.value

  activePackItem.value.iiko_product_unit = unit
  activePackItem.value.packaging_coefficient = coeff
  activePackItem.value.iiko_amount = targetAmount
  activePackItem.value.skip_knowledge_base = !savePackToKB.value

  const extra = {
    target_iiko_amount: targetAmount,
    packaging_coefficient: coeff,
    iiko_product_unit: unit,
    skip_knowledge_base: !savePackToKB.value
  }

  if (selectedContainerId.value) {
    activePackItem.value.iiko_container_id = selectedContainerId.value
    activePackItem.value.iiko_container_name = selectedContainerName.value
    extra.iiko_container_id = selectedContainerId.value
    extra.iiko_container_name = selectedContainerName.value
  }

  await updateItemValues(activePackItem.value, extra)
  packagingModalOpen.value = false
  toast.success('Пересчет фасовки успешно применен')
}

// Live Search Catalog Modal
const searchModalOpen = ref(false)
const activeSearchItem = ref(null)
const catalogQuery = ref('')
const catalogResults = ref([])
let catalogSearchTimeout = null

// Неточное распознавание текста
const isImpreciseRecognition = ref(false)
const editedRawName = ref('')
const skipKnowledgeBase = ref(false)

function openSearchFor(item) {
  activeSearchItem.value = item
  isImpreciseRecognition.value = !!item.is_imprecise_recognition
  editedRawName.value = item.raw_name || ''
  skipKnowledgeBase.value = !!item.skip_knowledge_base
  catalogQuery.value = item.clean_name || item.raw_name || ''
  searchModalOpen.value = true
  searchCatalog()
}

function onImpreciseToggle() {
  if (isImpreciseRecognition.value && !editedRawName.value) {
    editedRawName.value = activeSearchItem.value?.raw_name || ''
  }
}

function applyEditedText() {
  if (!editedRawName.value.trim() || !activeSearchItem.value) return
  activeSearchItem.value.raw_name = editedRawName.value.trim()
  activeSearchItem.value.clean_name = editedRawName.value.trim()
  activeSearchItem.value.is_imprecise_recognition = true
  catalogQuery.value = editedRawName.value.trim()
  searchCatalog()
  toast.info('Поиск обновлен по исправленному тексту')
}

async function quickSelectCandidate(item, cand) {
  item.iiko_product_id = cand.id
  item.iiko_product_name = cand.name
  item.iiko_product_code = cand.code
  item.iiko_product_unit = formatUnitName(cand.unit || 'кг')
  item.match_status = 'green'
  await updateItemValues(item)
  toast.success(`Привязано: ${cand.name}`)
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

  if (isImpreciseRecognition.value && editedRawName.value.trim()) {
    activeSearchItem.value.raw_name = editedRawName.value.trim()
    activeSearchItem.value.clean_name = editedRawName.value.trim()
  }
  activeSearchItem.value.is_imprecise_recognition = isImpreciseRecognition.value
  activeSearchItem.value.skip_knowledge_base = skipKnowledgeBase.value

  activeSearchItem.value.iiko_product_id = prod.id
  activeSearchItem.value.iiko_product_name = prod.name
  activeSearchItem.value.iiko_product_code = prod.code
  activeSearchItem.value.iiko_product_unit = formatUnitName(prod.unit || 'кг')
  activeSearchItem.value.match_status = 'green'
  await updateItemValues(activeSearchItem.value)
  searchModalOpen.value = false
  toast.success(`Сопоставлено: ${prod.name}`)
}

// Create Supplier Modal
const showSupplierModal = ref(false)
const creatingSupplier = ref(false)
const newSupplierForm = ref({ name: '', inn: '', code: '', phone: '' })

function openSupplierModal() {
  if (!newSupplierForm.value.name.trim() && invoice.value?.raw_supplier_name) {
    newSupplierForm.value.name = invoice.value.raw_supplier_name
    newSupplierForm.value.inn = invoice.value.raw_supplier_inn || ''
  }
  showSupplierModal.value = true
}

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
    newSupplierForm.value = { name: '', inn: '', code: '', phone: '' }
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

<style scoped>
.form-input {
  background-color: #020617; /* slate-950 */
  border: 1px solid #334155; /* slate-700 */
  color: #f8fafc;
  border-radius: 0.75rem;
  transition: all 0.15s ease-in-out;
  outline: none;
  color-scheme: dark;
}

.form-input:hover {
  border-color: #64748b; /* slate-500 */
}

.form-input:focus {
  border-color: #6366f1; /* indigo-500 */
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
}

.form-input::placeholder {
  color: #64748b;
}

select.form-input option {
  background-color: #0f172a;
  color: #f8fafc;
}
</style>
