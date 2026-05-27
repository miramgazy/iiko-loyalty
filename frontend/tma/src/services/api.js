import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 15000,
})

let _botUsername = null

/**
 * Set the bot username for the X-Bot-Username header
 */
export function setBotUsername(username) {
  _botUsername = username
}

// Request interceptor: attach JWT, X-Bot-Username, and cache-busting for GET
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('tma_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  if (_botUsername) {
    config.headers['X-Bot-Username'] = _botUsername
  }
  
  // Prevent aggressive caching on iOS WebKit/Safari
  if (config.method?.toLowerCase() === 'get') {
    config.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    config.headers['Pragma'] = 'no-cache'
    config.headers['Expires'] = '0'
    config.params = { ...config.params, _t: Date.now() }
  }
  
  return config
})

export default api
