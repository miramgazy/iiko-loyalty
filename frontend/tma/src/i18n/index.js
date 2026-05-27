import { ref } from 'vue'
import ru from '@/locales/ru.json'
import kz from '@/locales/kz.json'
import { safeStorage } from '@/services/storage'

export const locale = ref(safeStorage.getItem('tma_locale') || 'ru')

const translations = { ru, kz }

export function t(key) {
  return translations[locale.value]?.[key] || translations['ru']?.[key] || key
}

export function setLocale(lang) {
  if (translations[lang]) {
    locale.value = lang
    safeStorage.setItem('tma_locale', lang)
  }
}
