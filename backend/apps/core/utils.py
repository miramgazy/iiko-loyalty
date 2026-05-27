import re

def normalize_phone(phone_str: str) -> str:
    if not phone_str:
        return ""
    # Extract only digits
    digits = re.sub(r'\D', '', phone_str)
    # Handle leading 8 (typical in Russia/Kazakhstan)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    # If it's a 10-digit number without country code, assume it's Russia/Kazakhstan (+7)
    if len(digits) == 10:
        digits = '7' + digits
    return f"+{digits}"
