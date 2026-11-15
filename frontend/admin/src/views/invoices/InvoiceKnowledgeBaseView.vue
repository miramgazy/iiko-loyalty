<template>
  <div class="p-8 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button @click="$router.push('/admin/invoices')"
          class="w-9 h-9 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition-colors">
          ‹
        </button>
        <div>
          <h1 class="text-2xl font-bold text-white flex items-center gap-2">
            <span>🧠</span> База знаний сопоставления товаров
          </h1>
          <p class="text-slate-400 text-sm mt-1">
            Непрерывное самообучение: подтвержденные связки «Поставщик + Название из накладной ➔ Товар iiko»
          </p>
        </div>
      </div>

      <div class="relative w-72">
        <input
          v-model="searchQuery"
          @input="debounceSearch"
          type="text"
          placeholder="Поиск по поставщику или товару..."
          class="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
        />
        <span class="absolute right-3 top-2.5 text-slate-500 text-xs">🔍</span>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
      </div>

      <table v-else class="w-full text-left text-sm text-slate-300">
        <thead>
          <tr class="border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider bg-slate-950/40">
            <th class="px-6 py-4">Поставщик</th>
            <th class="px-6 py-4">Наименование в накладных (OCR)</th>
            <th class="px-6 py-4">Товар в iiko</th>
            <th class="px-6 py-4 text-center">Фасовка по умолч.</th>
            <th class="px-6 py-4 text-center">Применений</th>
            <th class="px-6 py-4 text-right">Посл. раз</th>
            <th class="px-6 py-4 text-right"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="alias in aliases" :key="alias.id" class="hover:bg-slate-850/50 transition-colors">
            <td class="px-6 py-4 font-medium text-white">
              {{ alias.supplier_name || 'Любой поставщик' }}
            </td>
            <td class="px-6 py-4">
              <span class="font-medium text-indigo-300 bg-indigo-950/40 border border-indigo-800/40 px-2 py-0.5 rounded text-xs">
                {{ alias.raw_product_name }}
              </span>
            </td>
            <td class="px-6 py-4">
              <div class="flex items-center gap-2">
                <span class="text-emerald-400">➔</span>
                <span class="font-bold text-white">{{ alias.iiko_product_name }}</span>
              </div>
            </td>
            <td class="px-6 py-4 text-center font-mono text-xs">
              {{ alias.default_packaging_coefficient }} {{ alias.default_container_name ? `(${alias.default_container_name})` : '' }}
            </td>
            <td class="px-6 py-4 text-center">
              <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-950/60 text-indigo-300 border border-indigo-800/60">
                {{ alias.usage_count }} раз
              </span>
            </td>
            <td class="px-6 py-4 text-right text-xs text-slate-400">
              {{ formatDate(alias.last_used_at) }}
            </td>
            <td class="px-6 py-4 text-right">
              <button
                @click="deleteAlias(alias)"
                class="text-xs text-rose-400 hover:text-rose-300 px-2.5 py-1 rounded-lg border border-rose-900/40 hover:bg-rose-900/30 transition-all"
              >
                Удалить
              </button>
            </td>
          </tr>
          <tr v-if="!aliases.length">
            <td colspan="7" class="px-6 py-16 text-center text-slate-500 text-sm">
              В базе знаний пока нет сохраненных связок.
              При каждой отправке проверенной накладной в iiko система автоматически обучается и пополняет эту базу.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const aliases = ref([])
const loading = ref(true)
const searchQuery = ref('')
let searchTimeout = null

async function loadAliases() {
  loading.value = true
  try {
    const res = await api.get('/invoices/knowledge-base/', {
      params: { organization_id: auth.currentOrgId, search: searchQuery.value || undefined }
    })
    aliases.value = res.data.results || res.data || []
  } catch {
    toast.error('Не удалось загрузить базу знаний')
  } finally {
    loading.value = false
  }
}

function debounceSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadAliases()
  }, 400)
}

async function deleteAlias(alias) {
  if (!confirm(`Удалить связку '${alias.raw_product_name} ➔ ${alias.iiko_product_name}'?`)) return
  try {
    await api.delete(`/invoices/knowledge-base/${alias.id}/`, {
      params: { organization_id: auth.currentOrgId }
    })
    aliases.value = aliases.value.filter(a => a.id !== alias.id)
    toast.success('Связка удалена из базы знаний')
  } catch {
    toast.error('Ошибка при удалении связки')
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('ru-RU')
}

onMounted(loadAliases)
</script>
