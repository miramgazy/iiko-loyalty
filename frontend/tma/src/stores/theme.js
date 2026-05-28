import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { applyThemeColors } from '@/services/telegram'
import { locale } from '@/i18n'

function getContrastColor(hexColor) {
  if (!hexColor) return '#ffffff'
  let hex = hexColor.replace('#', '')
  if (hex.length === 3) {
    hex = hex.split('').map(char => char + char).join('')
  }
  if (hex.length !== 6) return '#ffffff'
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.6 ? '#000000' : '#ffffff'
}

function hexToRgb(hexColor) {
  if (!hexColor) return null
  let hex = hexColor.replace('#', '')
  if (hex.length === 3) {
    hex = hex.split('').map(char => char + char).join('')
  }
  if (hex.length !== 6) return null
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  return { r, g, b }
}

function rgbToHex(r, g, b) {
  const clamp = (val) => Math.max(0, Math.min(255, val))
  return '#' + [r, g, b].map(x => {
    const hex = clamp(x).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('')
}

function updateThemeVariables(hexColor) {
  if (!hexColor) return
  document.documentElement.style.setProperty('--brand', hexColor)
  document.documentElement.style.setProperty('--gold', hexColor)
  
  // Calculate text contrast
  const contrast = getContrastColor(hexColor)
  document.documentElement.style.setProperty('--brand-text', contrast)
  document.documentElement.style.setProperty('--gold-text', contrast)

  // Calculate dark brand color (darken more if brand is light to keep high contrast)
  const rgb = hexToRgb(hexColor)
  if (rgb) {
    const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255
    const darkenFactor = luminance > 0.6 ? 0.50 : 0.80
    const darkR = Math.floor(rgb.r * darkenFactor)
    const darkG = Math.floor(rgb.g * darkenFactor)
    const darkB = Math.floor(rgb.b * darkenFactor)
    const darkHex = rgbToHex(darkR, darkG, darkB)
    document.documentElement.style.setProperty('--brand-dark', darkHex)
    document.documentElement.style.setProperty('--gold-dark', darkHex)

    // Calculate light brand color (blend towards white to lighten)
    const lightR = Math.min(255, Math.floor(rgb.r + (255 - rgb.r) * 0.3))
    const lightG = Math.min(255, Math.floor(rgb.g + (255 - rgb.g) * 0.3))
    const lightB = Math.min(255, Math.floor(rgb.b + (255 - rgb.b) * 0.3))
    const lightHex = rgbToHex(lightR, lightG, lightB)
    document.documentElement.style.setProperty('--gold-light', lightHex)

    // Gradients and glows
    document.documentElement.style.setProperty('--gold-gradient', `linear-gradient(135deg, ${hexColor} 0%, ${darkHex} 100%)`)
    document.documentElement.style.setProperty('--brand-glow', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.35)`)
    document.documentElement.style.setProperty('--gold-glow', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.40)`)
    document.documentElement.style.setProperty('--brand-10', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.10)`)
    document.documentElement.style.setProperty('--brand-15', `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0.15)`)
  }
}

export const useThemeStore = defineStore('tma-theme', () => {
  const primaryColor = ref('#6c5ce7')
  const greetingTextRu = ref('')
  const greetingTextKz = ref('')
  const logoUrl = ref(null)

  const greetingText = computed(() => {
    if (locale.value === 'kz') {
      return greetingTextKz.value || greetingTextRu.value || ''
    }
    return greetingTextRu.value || ''
  })

  // Apply default preview brand variables on init
  updateThemeVariables(primaryColor.value)

  function applyBranding(branding) {
    if (!branding) return

    if (branding.design_color) {
      primaryColor.value = branding.design_color
      document.documentElement.style.setProperty('--color-primary', branding.design_color)
      updateThemeVariables(branding.design_color)
      applyThemeColors(branding.design_color)
    } else {
      // Fall back to Telegram native colors
      const tg = window.Telegram?.WebApp
      const nativeColor = tg?.themeParams?.button_color || tg?.themeParams?.bg_color
      if (nativeColor) {
        primaryColor.value = nativeColor
        document.documentElement.style.setProperty('--color-primary', nativeColor)
        updateThemeVariables(nativeColor)
      }
    }

    if (branding.greeting_text) {
      greetingTextRu.value = branding.greeting_text
    } else {
      greetingTextRu.value = ''
    }

    if (branding.greeting_text_kz) {
      greetingTextKz.value = branding.greeting_text_kz
    } else {
      greetingTextKz.value = ''
    }

    if (branding.logo_url) {
      logoUrl.value = branding.logo_url
    }
  }

  return { primaryColor, greetingText, logoUrl, applyBranding }
})

