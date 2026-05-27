// Simple in-memory fallback database for restricted environments (like iOS iframe)
const memoryStorage = {}

export const safeStorage = {
  getItem(key) {
    try {
      return localStorage.getItem(key)
    } catch (e) {
      console.warn('localStorage is disabled or blocked. Falling back to memory.', e)
      return memoryStorage[key] || null
    }
  },
  
  setItem(key, value) {
    try {
      localStorage.setItem(key, value)
    } catch (e) {
      console.warn('localStorage is disabled or blocked. Falling back to memory.', e)
      memoryStorage[key] = String(value)
    }
  },
  
  removeItem(key) {
    try {
      localStorage.removeItem(key)
    } catch (e) {
      console.warn('localStorage is disabled or blocked. Falling back to memory.', e)
      delete memoryStorage[key]
    }
  },
  
  clear() {
    try {
      localStorage.clear()
    } catch (e) {
      console.warn('localStorage is disabled or blocked. Falling back to memory.', e)
      for (const key in memoryStorage) {
        delete memoryStorage[key]
      }
    }
  }
}
