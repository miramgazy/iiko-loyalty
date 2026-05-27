/**
 * Telegram WebApp SDK initialization helper
 */
export function initTelegramWebApp() {
  const tg = window.Telegram?.WebApp
  if (!tg) {
    console.warn('Telegram WebApp SDK not available')
    return null
  }
  tg.ready()
  tg.expand()
  return tg
}

/**
 * Get the bot username from Telegram init data
 */
export function getBotUsername() {
  const tg = window.Telegram?.WebApp
  if (!tg) return null
  
  // Try receiver (when opened via inline button)
  const receiver = tg.initDataUnsafe?.receiver?.username
  if (receiver) return receiver
  
  // Try extracting from startapp or start_param
  const startParam = tg.initDataUnsafe?.start_param
  if (startParam) return startParam

  // Fallback: parse from URL query param
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('bot_username') || null
}

/**
 * Get raw init data string for backend validation
 */
export function getInitData() {
  return window.Telegram?.WebApp?.initData || ''
}

/**
 * Request user's phone contact via native Telegram dialog
 * Returns a promise
 */
export function requestContact() {
  return new Promise((resolve, reject) => {
    const tg = window.Telegram?.WebApp
    if (!tg) return reject(new Error('Telegram WebApp SDK not available'))

    if (typeof tg.requestContact === 'function') {
      const handler = (event) => {
        if (tg.offEvent) {
          tg.offEvent('contactRequested', handler)
        }
        if (event && event.status === 'sent') {
          resolve(true)
        } else {
          reject(new Error('User declined contact sharing'))
        }
      }

      if (tg.onEvent) {
        tg.onEvent('contactRequested', handler)
      }

      tg.requestContact((shared) => {
        // Fallback for direct callback support on some client versions
        if (shared) {
          if (tg.offEvent) {
            tg.offEvent('contactRequested', handler)
          }
          resolve(true)
        }
      })
    } else {
      // Fallback for older clients: use MainButton
      const mainButton = tg.MainButton
      mainButton.setText('Поделиться контактом')
      mainButton.setParams?.({ request_contact: true })
      mainButton.show()
      mainButton.onClick(() => {
        resolve(true)
        mainButton.hide()
      })
    }
  })
}

/**
 * Set TMA header and background color
 */
export function applyThemeColors(hexColor) {
  const tg = window.Telegram?.WebApp
  if (!tg) return
  try {
    tg.setHeaderColor(hexColor || 'bg_color')
    tg.setBackgroundColor(hexColor || 'bg_color')
  } catch (e) {
    console.warn('Could not apply theme colors:', e)
  }
}
