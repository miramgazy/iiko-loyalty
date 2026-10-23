import random
import string
import re
from apps.loyalty.models import Customer

# Emojis regex pattern
EMOJI_PATTERN = re.compile(
    r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf\u200d\ufe0f]',
    flags=re.UNICODE
)

# Forbidden symbols: digits, punctuation, special characters
FORBIDDEN_NAME_PATTERN = re.compile(r'[0-9._,;:!?@#$%^&*()+={}\[\]<>~`|\\/]')

# Allowed letters: Latin, Cyrillic (including Kazakh Әә, Іі, Ңң, Ғғ, Үү, Ұұ, Ққ, Өө, Һһ), spaces, hyphens, apostrophes
ALLOWED_NAME_PATTERN = re.compile(r'^[a-zA-Z\u0400-\u04FF\u0500-\u052F\s\-’\']+$')

def is_valid_name(val, required: bool = False) -> bool:
    if val is None:
        return not required
    s = str(val).strip()
    if not s:
        return not required
    if s.lower() in ('гость', 'guest'):
        return False
    if FORBIDDEN_NAME_PATTERN.search(s):
        return False
    if EMOJI_PATTERN.search(s):
        return False
    if not ALLOWED_NAME_PATTERN.match(s):
        return False
    letters = re.sub(r'[^a-zA-Z\u0400-\u04FF\u0500-\u052F]', '', s)
    if len(letters) < 2:
        return False
    return True

def generate_unique_card_number(organization, length=10):
    while True:
        card_number = ''.join(random.choices(string.digits, k=length))
        if card_number.startswith('0'):
            continue
        if not Customer.objects.filter(organization=organization, iiko_card_number=card_number).exists():
            return card_number
