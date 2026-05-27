import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const refreshToken = ref(localStorage.getItem('refresh_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const currentOrgId = ref(localStorage.getItem('current_org_id') || null)

  const isAuthenticated = computed(() => !!accessToken.value)

  const isSuperAdmin = computed(() => {
    if (!user.value) return false
    if (user.value.is_superuser) return true
    return user.value.memberships?.some(m =>
      m.role === 'superuser' || m.role === 'superadmin'
    )
  })

  const currentMembership = computed(() => {
    if (!user.value || !currentOrgId.value) return null
    return user.value.memberships?.find(m => String(m.organization.id) === String(currentOrgId.value)) || null
  })

  const currentRole = computed(() => currentMembership.value?.role || null)

  const isOrgManager = computed(() => {
    if (isSuperAdmin.value) return true
    return currentRole.value === 'org_manager'
  })

  const isOrgAdmin = computed(() => {
    if (isOrgManager.value) return true
    return currentRole.value === 'org_admin'
  })

  async function login(username, password) {
    const res = await axios.post(`${API_BASE}/accounts/token/`, { username, password })
    accessToken.value = res.data.access
    refreshToken.value = res.data.refresh
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    localStorage.setItem('user', JSON.stringify(res.data.user))

    // Auto-select org if only one membership
    const memberships = res.data.user.memberships || []
    if (memberships.length === 1) {
      setCurrentOrg(memberships[0].organization.id)
    }
    return res.data
  }

  async function refreshAccessToken() {
    const res = await axios.post(`${API_BASE}/accounts/token/refresh/`, {
      refresh: refreshToken.value,
    })
    accessToken.value = res.data.access
    localStorage.setItem('access_token', res.data.access)
  }

  function setCurrentOrg(orgId) {
    currentOrgId.value = String(orgId)
    localStorage.setItem('current_org_id', String(orgId))
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null
    currentOrgId.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('current_org_id')
  }

  return {
    accessToken, refreshToken, user, currentOrgId,
    isAuthenticated, isSuperAdmin, currentMembership, currentRole,
    isOrgManager, isOrgAdmin,
    login, refreshAccessToken, setCurrentOrg, logout,
  }
})
