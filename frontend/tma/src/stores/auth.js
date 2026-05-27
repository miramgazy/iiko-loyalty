import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import { getInitData, getBotUsername } from '@/services/telegram'
import { setBotUsername } from '@/services/api'
import { safeStorage } from '@/services/storage'

export const useAuthStore = defineStore('tma-auth', () => {
  const accessToken = ref(safeStorage.getItem('tma_access_token') || null)
  const refreshToken = ref(safeStorage.getItem('tma_refresh_token') || null)
  const customer = ref(JSON.parse(safeStorage.getItem('tma_customer') || 'null'))
  const organization = ref(JSON.parse(safeStorage.getItem('tma_organization') || 'null'))
  const botUsername = ref(null)
  const authError = ref(null)
  const isLoading = ref(true)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isOnboarded = computed(() => !!customer.value?.is_onboarded || !!customer.value?.phone)
  const needsConsent = computed(() => customer.value?.is_bot_subscribed == null)

  async function authenticate() {
    isLoading.value = true
    authError.value = null

    try {
      const initData = getInitData()
      const username = getBotUsername()
      botUsername.value = username

      if (username) {
        setBotUsername(username)
      }

      if (!initData) {
        authError.value = 'Telegram initData not available. Open this app from Telegram.'
        isLoading.value = false
        return false
      }

      const res = await api.post('/loyalty/tma/auth/', {
        initData,
        bot_username: username,
      })

      accessToken.value = res.data.access
      refreshToken.value = res.data.refresh
      customer.value = res.data.customer
      organization.value = res.data.organization

      safeStorage.setItem('tma_access_token', res.data.access)
      safeStorage.setItem('tma_refresh_token', res.data.refresh)
      safeStorage.setItem('tma_customer', JSON.stringify(res.data.customer))
      safeStorage.setItem('tma_organization', JSON.stringify(res.data.organization))

      return true
    } catch (e) {
      authError.value = e.response?.data?.error || 'Authentication failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  function updateCustomer(data) {
    customer.value = { ...customer.value, ...data }
    safeStorage.setItem('tma_customer', JSON.stringify(customer.value))
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    customer.value = null
    organization.value = null
    safeStorage.removeItem('tma_access_token')
    safeStorage.removeItem('tma_refresh_token')
    safeStorage.removeItem('tma_customer')
    safeStorage.removeItem('tma_organization')
  }

  return {
    accessToken, refreshToken, customer, organization,
    botUsername, authError, isLoading,
    isAuthenticated, isOnboarded, needsConsent,
    authenticate, updateCustomer, logout,
  }
})
