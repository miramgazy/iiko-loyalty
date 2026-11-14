import random
import string
import re
import logging
from apps.loyalty.models import Customer

logger = logging.getLogger(__name__)

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


def ensure_customer_card_in_iiko(customer, service=None, guest_info=None):
    """
    Ensures that customer has an iiko_card_number in the local database AND registered in iikoCard.
    1. If iikoCard already has cards for this customer, sync the first one to local DB.
    2. If iikoCard has no card for this customer:
       - Use customer.iiko_card_number if set, or generate a new unique one.
       - Register it in iikoCard via service.add_virtual_card.
       - Save to customer.iiko_card_number.
    """
    if not customer or not customer.iiko_customer_id:
        return customer.iiko_card_number if customer else None

    org = customer.organization
    if not service:
        from apps.loyalty.services import get_iiko_service
        service = get_iiko_service(org)

    # 1. Check existing cards in iiko
    cards = guest_info.get("cards", []) if guest_info else []
    if not cards and not guest_info:
        try:
            info = service.get_customer_info_by_id(customer.iiko_customer_id)
            if info:
                cards = info.get("cards", [])
        except Exception as e:
            logger.warning(f"Could not fetch cards for customer {customer.id} from iiko: {e}")

    iiko_card_numbers = [str(c.get("number")) for c in cards if c.get("number")]

    # If iikoCard already has a card for this customer:
    if iiko_card_numbers:
        if not customer.iiko_card_number or str(customer.iiko_card_number) not in iiko_card_numbers:
            customer.iiko_card_number = iiko_card_numbers[0]
            customer.save(update_fields=['iiko_card_number'])
            logger.info(f"Customer {customer.id} synced card {customer.iiko_card_number} from iiko")
        return customer.iiko_card_number

    # 2. iikoCard has no card for this customer -> Generate and upload to iikoCard
    card_number = customer.iiko_card_number
    if not card_number:
        card_number = generate_unique_card_number(org)
        customer.iiko_card_number = card_number
        customer.save(update_fields=['iiko_card_number'])
        logger.info(f"Generated new card {card_number} for customer {customer.id}")

    try:
        service.add_virtual_card(customer.iiko_customer_id, str(card_number))
        logger.info(f"Successfully uploaded virtual card {card_number} to iikoCard for customer {customer.id} ({customer.iiko_customer_id})")
    except Exception as e:
        logger.warning(f"Error registering card {card_number} in iiko: {e}. Retrying with fresh number...")
        try:
            fresh_card = generate_unique_card_number(org)
            customer.iiko_card_number = fresh_card
            customer.save(update_fields=['iiko_card_number'])
            service.add_virtual_card(customer.iiko_customer_id, str(fresh_card))
            logger.info(f"Successfully uploaded retry card {fresh_card} to iikoCard for customer {customer.id}")
            return fresh_card
        except Exception as retry_err:
            logger.error(f"Failed to register retry card in iiko for customer {customer.id}: {retry_err}")

    return customer.iiko_card_number


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
