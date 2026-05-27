/**
 * Normalizes a phone number string to +7XXXXXXXXXX format
 */
export function normalizePhone(phone) {
  const digits = phone.replace(/\D/g, '')
  if (digits.startsWith('8') && digits.length === 11) {
    return `+7${digits.slice(1)}`
  }
  if (digits.startsWith('7') && digits.length === 11) {
    return `+${digits}`
  }
  if (digits.length === 10) {
    return `+7${digits}`
  }
  return `+${digits}`
}
