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


def resolve_customer_tier(customer, org=None, active_wallet_name=None):
    """
    Resolves the customer's loyalty tier, styling, badge and colors
    according to organization's client_classification_settings.
    Single Source of Truth across TMA, Web Onboarding, Customer List, and Wallets.
    """
    if customer is None and org is None:
        return None

    if org is None and customer:
        org = customer.organization

    if not org:
        return None

    brand_color = org.brand_color or '#6366f1'
    org_banner_url = (org.apple_wallet_settings or {}).get('strip_url') or (org.google_wallet_settings or {}).get('hero_image_url')

    # If classification is disabled, return base default pass using unified brand_color
    if not org.is_client_classification_enabled:
        return {
            "is_classification_enabled": False,
            "tier_id": "base",
            "name": "Базовый",
            "name_kz": "Базалық",
            "badge": "Loyalty Pass",
            "color": brand_color,
            "gradient_preset": "brand",
            "cashback_percent": None,
            "description": "",
            "banner_url": org_banner_url
        }

    settings = org.client_classification_settings or {}
    tiers = settings.get('tiers', [])

    if not tiers or not isinstance(tiers, list):
        return {
            "is_classification_enabled": True,
            "tier_id": "base",
            "name": "Базовый",
            "name_kz": "Базалық",
            "badge": "Loyalty Pass",
            "color": brand_color,
            "gradient_preset": "brand",
            "cashback_percent": None,
            "description": "",
            "banner_url": org_banner_url
        }

    # Gather search candidate strings from customer
    search_strings = []
    if active_wallet_name:
        search_strings.append(str(active_wallet_name))

    if customer:
        try:
            for w in customer.wallets.all():
                if w.name:
                    search_strings.append(str(w.name))
        except Exception:
            pass

        if isinstance(customer.iiko_categories, list):
            for cat in customer.iiko_categories:
                if isinstance(cat, dict) and cat.get('name'):
                    search_strings.append(str(cat.get('name')))

    search_lowers = [s.strip().lower() for s in search_strings if s and s.strip()]

    # Match against configured tiers
    for tier in tiers:
        if not isinstance(tier, dict):
            continue

        tier_banner = tier.get('banner_url') or tier.get('strip_url') or tier.get('hero_image_url') or org_banner_url

        # Match 1: By exact or substring iiko wallet name
        iiko_w_name = tier.get('iiko_wallet_name')
        if iiko_w_name and str(iiko_w_name).strip():
            w_target = str(iiko_w_name).strip().lower()
            if any(w_target in s for s in search_lowers):
                return {
                    "is_classification_enabled": True,
                    "tier_id": tier.get('id') or f"tier_{tier.get('name', '')}",
                    "name": tier.get('name', 'Уровень'),
                    "name_kz": tier.get('name_kz') or tier.get('name', 'Уровень'),
                    "badge": tier.get('badge') or f"{tier.get('name', '')} Pass",
                    "color": tier.get('color') or brand_color,
                    "gradient_preset": tier.get('gradient_preset', 'brand'),
                    "cashback_percent": tier.get('cashback_percent'),
                    "description": tier.get('description', ''),
                    "banner_url": tier_banner
                }

        # Match 2: By comma-separated or list of keywords
        keywords = tier.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        if isinstance(keywords, list) and keywords:
            for kw in keywords:
                kw_str = str(kw).strip().lower()
                if kw_str and any(kw_str in s for s in search_lowers):
                    return {
                        "is_classification_enabled": True,
                        "tier_id": tier.get('id') or f"tier_{tier.get('name', '')}",
                        "name": tier.get('name', 'Уровень'),
                        "name_kz": tier.get('name_kz') or tier.get('name', 'Уровень'),
                        "badge": tier.get('badge') or f"{tier.get('name', '')} Pass",
                        "color": tier.get('color') or brand_color,
                        "gradient_preset": tier.get('gradient_preset', 'brand'),
                        "cashback_percent": tier.get('cashback_percent'),
                        "description": tier.get('description', ''),
                        "banner_url": tier_banner
                    }

    # If no tier matched, fallback to default base tier
    return {
        "is_classification_enabled": True,
        "tier_id": "default",
        "name": "Базовый",
        "name_kz": "Базалық",
        "badge": "Loyalty Pass",
        "color": brand_color,
        "gradient_preset": "brand",
        "cashback_percent": None,
        "description": "",
        "banner_url": org_banner_url
    }
