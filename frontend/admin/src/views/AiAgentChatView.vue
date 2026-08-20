<template>
  <div class="p-8 h-[85vh] flex flex-col justify-between">
    <!-- Header -->
    <div class="mb-4 flex-shrink-0 flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-2">
          <span>🤖</span> AI Финансовый Аналитик & Закупщик
        </h1>
        <p class="text-slate-400 text-sm mt-1">Чат-интерфейс для анализа выручки, инфляции сырья, Min-Max остатков и планирования закупок.</p>
      </div>
      <button 
        v-if="messages.length" 
        @click="clearChat" 
        class="px-4 py-2 bg-slate-800 hover:bg-slate-700 hover:text-white text-slate-300 border border-slate-700/60 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5"
      >
        <span>🗑️</span> Очистить чат
      </button>
    </div>

    <!-- Messages Container -->
    <div class="flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 overflow-y-auto mb-6 flex flex-col gap-4" ref="messagesContainer">
      <div v-for="(msg, idx) in messages" :key="idx" class="flex"
        :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
        
        <div class="max-w-[70%] rounded-2xl px-5 py-3 text-sm leading-relaxed"
          :class="msg.role === 'user' 
            ? 'bg-indigo-650 text-white rounded-br-none shadow-md shadow-indigo-600/10' 
            : 'bg-slate-800 text-slate-100 rounded-bl-none border border-slate-700/50'">
          
          <p class="whitespace-pre-line">{{ msg.content }}</p>
        </div>
      </div>
      
      <!-- Typing indicator -->
      <div v-if="sending" class="flex justify-start">
        <div class="bg-slate-800 text-slate-100 rounded-2xl rounded-bl-none border border-slate-700/50 px-5 py-4 flex gap-1.5 items-center">
          <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
      </div>
      
      <div v-if="!messages.length" class="flex-1 flex flex-col items-center justify-center text-center text-slate-500">
        <span class="text-5xl mb-4">💬</span>
        <p class="font-semibold text-white mb-2">Начните диалог с AI-помощником</p>
        <p class="text-xs max-w-sm">Спросите: "Какие наши KPI на сегодня?", "Покажи упущенную выручку по стоп-листам" или "Сформируй заказ сырья на кухню".</p>
      </div>
    </div>

    <!-- Input Box -->
    <form @submit.prevent="sendMessage" class="flex gap-3 flex-shrink-0">
      <input 
        v-model="inputMsg" 
        type="text" 
        placeholder="Задайте вопрос AI-агенту..." 
        :disabled="sending"
        class="flex-1 bg-slate-900 border border-slate-800 text-white rounded-xl px-5 py-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder:text-slate-500" 
      />
      <button 
        type="submit" 
        :disabled="sending || !inputMsg.trim()"
        class="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-6 py-4 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center"
      >
        <span>Отправить</span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useToastStore } from '@/stores/toast'

const auth = useAuthStore()
const toast = useToastStore()

const inputMsg = ref('')
const sending = ref(false)
const messages = ref([])
const messagesContainer = ref(null)

const cacheKey = computed(() => {
  const userId = auth.user?.id || 'default'
  const orgId = auth.currentOrgId || 'default'
  return `iiko_chat_history_${userId}_${orgId}`
})

onMounted(() => {
  const cached = localStorage.getItem(cacheKey.value)
  if (cached) {
    try {
      messages.value = JSON.parse(cached)
      scrollToBottom()
    } catch (e) {
      console.error('Failed to parse cached chat history', e)
    }
  }
})

function saveHistory() {
  localStorage.setItem(cacheKey.value, JSON.stringify(messages.value))
}

function clearChat() {
  messages.value = []
  localStorage.removeItem(cacheKey.value)
}

async function sendMessage() {
  if (!inputMsg.value.trim() || sending.value) return
  
  const text = inputMsg.value.trim()
  inputMsg.value = ''
  
  // Add user message
  messages.value.push({ role: 'user', content: text })
  saveHistory()
  scrollToBottom()
  
  sending.value = true
  try {
    const orgId = auth.currentOrgId
    const res = await api.post(`/ai_agent/organizations/${orgId}/chat/`, {
      messages: messages.value
    })
    
    // Add assistant response
    messages.value.push({ role: 'assistant', content: res.data.response })
  } catch (e) {
    const errorMsg = e.response?.data?.error || 'Не удалось связаться с AI-агентом'
    toast.error(errorMsg)
    // Remove last message if failed or just show error
    messages.value.push({ role: 'assistant', content: `❌ Ошибка: ${errorMsg}` })
  } finally {
    saveHistory()
    sending.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}
</script>
