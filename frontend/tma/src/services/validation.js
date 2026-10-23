/**
 * Name validation utility for TMA.
 * Checks whether first name and last name contain real names without invalid characters
 * such as single dots, emojis, numbers, special symbols, etc.
 */

// Matches any emoji sequence or pictographs
const EMOJI_REGEX = /\p{Extended_Pictographic}/u

// Allowed letters: Latin, Cyrillic (Russian + Kazakh letters like Әә, Іі, Ңң, Ғғ, Үү, Ұұ, Ққ, Өө, Һһ)
const ALLOWED_CHARS_REGEX = /^[a-zA-Z\u0400-\u04FF\u0500-\u052F\s\-’']+$/u

// Forbidden symbols (dots, punctuation, special chars, numbers)
const FORBIDDEN_SYMBOLS_REGEX = /[0-9._,;:!?@#$%^&*()+={}\[\]<>~`|\\/]/

export function isValidName(val, required = false) {
  if (val === null || val === undefined) {
    return !required
  }
  const str = String(val).trim()
  if (!str) {
    return !required
  }

  // Reject placeholder names like "Гость" / "Guest"
  const lower = str.toLowerCase()
  if (lower === 'гость' || lower === 'guest') {
    return false
  }

  // Must not contain forbidden symbols (dots, numbers, underscores, etc.)
  if (FORBIDDEN_SYMBOLS_REGEX.test(str)) {
    return false
  }

  // Must not contain emojis
  if (EMOJI_REGEX.test(str)) {
    return false
  }

  // Must only contain letters, spaces, hyphens, apostrophes
  if (!ALLOWED_CHARS_REGEX.test(str)) {
    return false
  }

  // Must contain at least 2 letters
  const lettersOnly = str.replace(/[^a-zA-Z\u0400-\u04FF\u0500-\u052F]/gu, '')
  if (lettersOnly.length < 2) {
    return false
  }

  return true
}

export function validateCustomerName(customer) {
  const firstName = customer?.first_name || ''
  const lastName = customer?.last_name || ''

  const isFirstValid = isValidName(firstName, true)
  const isLastValid = isValidName(lastName, false)

  return {
    isValid: isFirstValid && isLastValid,
    isFirstValid,
    isLastValid,
  }
}
