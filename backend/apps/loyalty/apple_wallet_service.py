import io
import os
import json
import zlib
import struct
import hashlib
import logging
import zipfile
from typing import Optional, Dict, Any, Tuple

from django.conf import settings
from django.core import signing
from django.core.files.storage import default_storage

from apps.core.models import Organization
from apps.loyalty.models import Customer
from apps.loyalty.utils import generate_unique_card_number, resolve_customer_tier

logger = logging.getLogger(__name__)


def hex_to_rgb(hex_str: Optional[str], default: str = "rgb(24, 24, 27)") -> str:
    """Converts HEX color (#RRGGBB or #RGB) to Apple Wallet 'rgb(R, G, B)' format."""
    if not hex_str:
        return default
    s = str(hex_str).strip().lstrip('#')
    if len(s) == 3:
        s = ''.join(c * 2 for c in s)
    if len(s) != 6:
        return default
    try:
        r = int(s[0:2], 16)
        g = int(s[2:4], 16)
        b = int(s[4:6], 16)
        return f"rgb({r}, {g}, {b})"
    except (ValueError, IndexError):
        return default


def generate_png_bytes(width: int = 1, height: int = 1, r: int = 24, g: int = 24, b: int = 27, a: int = 255) -> bytes:
    """
    Generates minimal valid uncompressed RGBA PNG image bytes in pure Python
    without external dependencies (e.g. Pillow).
    Used as fallback default assets for icon/logo/strip.
    """
    raw_data = bytes([0] + [r, g, b, a] * width) * height

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xffffffff)

    ihdr = struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw_data)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


class AppleWalletService:
    """
    Multi-tenant service for issuing and updating Apple Wallet passes (.pkpass).
    Supports a single master Apple Developer Account (Team ID & Pass Type ID)
    serving multiple organizations/restaurants dynamically, with unified card numbers
    matching iiko_card_number.
    """

    def __init__(self):
        # Master issuer settings (from settings / environment)
        self.default_pass_type_id = (
            getattr(settings, 'APPLE_PASS_TYPE_ID', None)
            or os.environ.get('APPLE_PASS_TYPE_ID', 'pass.kz.loyalty.service')
        )
        self.default_team_id = (
            getattr(settings, 'APPLE_TEAM_ID', None)
            or os.environ.get('APPLE_TEAM_ID', 'APPLE_TEAM_ID')
        )

        # Signing certificates (Pass certificate + Private key + WWDR CA)
        self.p12_data = self._load_cert_data('APPLE_P12_BASE64', 'APPLE_P12_BASE64')
        self.cert_pem = self._load_cert_data('APPLE_CERTIFICATE_PEM', 'APPLE_CERTIFICATE_BASE64')
        self.key_pem = self._load_cert_data('APPLE_KEY_PEM', 'APPLE_KEY_BASE64')
        self.wwdr_pem = self._load_cert_data('APPLE_WWDR_PEM', 'APPLE_WWDR_BASE64')
        self.key_password = getattr(settings, 'APPLE_CERTIFICATE_PASSWORD', None) or os.environ.get('APPLE_CERTIFICATE_PASSWORD')

        # Auto-extract PEM cert and private key from PKCS#12 bundle if needed (for APNs mTLS & signing)
        if self.p12_data and (not self.cert_pem or not self.key_pem):
            try:
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.serialization import pkcs12
                password = self.key_password.encode('utf-8') if self.key_password else None
                private_key, signer_cert, _ = pkcs12.load_key_and_certificates(self.p12_data, password=password)
                if signer_cert and not self.cert_pem:
                    self.cert_pem = signer_cert.public_bytes(serialization.Encoding.PEM)
                if private_key and not self.key_pem:
                    self.key_pem = private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    )
            except Exception as e:
                logger.warning(f"Could not extract PEM cert/key from p12 bundle: {e}")

    def _load_cert_data(self, env_pem_key: str, env_b64_key: str) -> Optional[bytes]:
        """Loads PEM/DER cert bytes from settings, env or base64 env."""
        val = getattr(settings, env_pem_key, None) or os.environ.get(env_pem_key)
        if val and not env_pem_key.endswith('_BASE64'):
            return val.encode('utf-8') if isinstance(val, str) else val

        import base64
        b64_val = getattr(settings, env_b64_key, None) or os.environ.get(env_b64_key)
        if b64_val:
            try:
                clean_b64 = str(b64_val).strip().replace('\n', '').replace('\r', '').replace(' ', '')
                return base64.b64decode(clean_b64)
            except Exception as e:
                logger.warning(f"Failed to decode base64 for {env_b64_key}: {e}")
        return None

    @property
    def is_signing_configured(self) -> bool:
        """Checks if real Apple Developer certificates are installed."""
        return bool(self.p12_data or (self.cert_pem and (self.key_pem or self.cert_pem)))

    def get_pass_type_id(self, org: Organization) -> str:
        """Returns Pass Type ID for the organization (falls back to master pass type id)."""
        return org.apple_pass_type_id or self.default_pass_type_id

    def get_team_id(self, org: Organization) -> str:
        """Returns Apple Team ID (falls back to master team id)."""
        return org.apple_team_id or self.default_team_id

    def get_auth_token(self, customer: Customer) -> str:
        """Generates static authentication token for PassKit Web Service dynamic updates."""
        secret = getattr(settings, 'SECRET_KEY', 'default-secret-key')
        raw = f"{customer.id}:{customer.organization_id}:{secret}"
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def verify_auth_token(self, customer: Customer, auth_token: str) -> bool:
        """Verifies ApplePass Authorization header token matches customer's expected token."""
        if not auth_token:
            return False
        clean_token = auth_token.strip()
        if clean_token.startswith("ApplePass "):
            clean_token = clean_token.split(" ", 1)[1].strip()
        expected = self.get_auth_token(customer)
        return clean_token == expected

    def send_pass_update_push(self, customer: Customer) -> int:
        """
        Sends APNs push notifications to all registered Apple devices for this customer.
        Each device receives an empty payload {} on topic {pass_type_id}.
        Returns the number of devices successfully notified.
        """
        from apps.loyalty.models import AppleWalletDeviceRegistration
        registrations = list(AppleWalletDeviceRegistration.objects.filter(customer=customer))
        if not registrations:
            logger.info(f"Apple Wallet: no registered devices found for customer id={customer.id}. Push skipped.")
            return 0

        if not self.is_signing_configured or not self.cert_pem:
            logger.info(f"Apple Wallet certs not configured. Mocking APNs push to {len(registrations)} device(s).")
            return len(registrations)

        # Bump timestamps so PassKit protocol detects changes
        from django.utils import timezone
        now = timezone.now()
        AppleWalletDeviceRegistration.objects.filter(customer=customer).update(updated_at=now)
        Customer.objects.filter(id=customer.id).update(updated_at=now)

        success_count = 0
        use_sandbox = getattr(settings, 'APPLE_APNS_SANDBOX', False)
        apns_host = "api.sandbox.push.apple.com" if use_sandbox else "api.push.apple.com"

        import tempfile
        import subprocess

        try:
            with tempfile.NamedTemporaryFile('wb', suffix='.pem') as cert_file, \
                 tempfile.NamedTemporaryFile('wb', suffix='.pem') as key_file:

                cert_file.write(self.cert_pem)
                cert_file.flush()

                key_data = self.key_pem or self.cert_pem
                key_file.write(key_data)
                key_file.flush()

                httpx_client = None
                try:
                    import httpx
                    httpx_client = httpx.Client(
                        cert=(cert_file.name, key_file.name),
                        http2=True,
                        timeout=5.0
                    )
                except Exception as ex_client:
                    logger.debug(f"httpx HTTP/2 client unavailable ({ex_client}), falling back to curl --http2")

                for reg in registrations:
                    url = f"https://{apns_host}/3/device/{reg.push_token}"
                    topic = reg.pass_type_identifier

                    if httpx_client:
                        headers = {
                            "apns-topic": topic,
                            "apns-push-type": "background",
                            "apns-priority": "5"
                        }
                        try:
                            resp = httpx_client.post(url, headers=headers, json={})
                            if resp.status_code == 200:
                                success_count += 1
                                logger.info(f"APNs push delivered to device {reg.device_library_identifier[:8]}...")
                            elif resp.status_code in (410, 404):
                                logger.info(f"Device {reg.device_library_identifier} unregistered by APNs. Removing.")
                                reg.delete()
                            else:
                                logger.warning(f"APNs response {resp.status_code} for device {reg.device_library_identifier}: {resp.text}")
                        except Exception as e:
                            logger.warning(f"Failed to post to APNs via httpx for device {reg.device_library_identifier}: {e}")
                    else:
                        # Fallback to system curl with native HTTP/2
                        try:
                            cmd = [
                                "curl", "-s", "-i", "--http2",
                                "-d", "{}",
                                "-H", f"apns-topic: {topic}",
                                "-H", "apns-push-type: background",
                                "-H", "apns-priority: 5",
                                "--cert", cert_file.name,
                                "--key", key_file.name,
                                "--max-time", "5",
                                url
                            ]
                            proc = subprocess.run(cmd, capture_output=True, text=True)
                            status_line = proc.stdout.splitlines()[0] if proc.stdout else ""
                            if "200" in status_line:
                                success_count += 1
                                logger.info(f"APNs push delivered via curl to device {reg.device_library_identifier[:8]}...")
                            elif "410" in status_line or "404" in status_line:
                                logger.info(f"Device {reg.device_library_identifier} unregistered by APNs. Removing.")
                                reg.delete()
                            else:
                                logger.warning(f"curl APNs output for device {reg.device_library_identifier}: {status_line}")
                        except Exception as e:
                            logger.warning(f"Failed to post to APNs via curl for device {reg.device_library_identifier}: {e}")

                if httpx_client:
                    httpx_client.close()

        except Exception as ex:
            logger.warning(f"Error setting up APNs push client: {ex}")

        return success_count

    def send_broadcast_push(self, customer: Customer, message: str, task_id: Optional[int] = None) -> int:
        """
        Sends an Apple Wallet broadcast push notification for marketing or announcements.
        Stores the broadcast message in cache so the updated pass contains a new 'broadcast_notice' field.
        When iOS downloads the updated pass, the change in this field automatically triggers
        a lock-screen push notification on the user's iPhone with the message text!
        """
        from django.core.cache import cache
        clean_msg = message.strip()
        try:
            cache.set(f"apple_wallet_broadcast_{customer.id}", clean_msg, timeout=86400 * 30)
        except Exception as e:
            logger.warning(f"Could not cache broadcast message for customer {customer.id}: {e}")

        # Trigger APNs push to notify registered devices to fetch the new pass
        return self.send_pass_update_push(customer)

    def build_pass_json(self, customer: Customer) -> Dict[str, Any]:
        """
        Builds the complete pass.json structure for an organization's loyalty card.
        Multi-tenant: dynamically populated with organization branding and tier data.
        Card number: strictly uses customer.iiko_card_number (or wallet_barcode).
        """
        org = customer.organization
        pass_type_id = self.get_pass_type_id(org)
        team_id = self.get_team_id(org)

        # Ensure customer has iiko_card_number
        if not customer.iiko_card_number:
            customer.iiko_card_number = generate_unique_card_number(org)
            customer.save(update_fields=['iiko_card_number'])

        card_number = str(customer.iiko_card_number)
        serial_number = f"{org.slug}_{customer.id}"

        # Resolve loyalty program name from iiko card / customer wallets / iiko categories / tier
        loyalty_program_name = None
        try:
            primary_wallet = customer.wallets.order_by('-balance').first()
            if primary_wallet and primary_wallet.name and primary_wallet.name.strip():
                loyalty_program_name = primary_wallet.name.strip()
        except Exception:
            pass

        if not loyalty_program_name and customer.iiko_categories and isinstance(customer.iiko_categories, list):
            for cat in customer.iiko_categories:
                if isinstance(cat, dict) and cat.get('name') and str(cat.get('name')).strip():
                    loyalty_program_name = str(cat.get('name')).strip()
                    break
                elif isinstance(cat, str) and cat.strip():
                    loyalty_program_name = cat.strip()
                    break

        tier_info = resolve_customer_tier(customer, org)
        if not loyalty_program_name:
            loyalty_program_name = (tier_info.get('name') if tier_info else None) or "Базовый"

        cashback_percent = tier_info.get('cashback_percent') if tier_info else None

        # Colors from tier or organization settings or brand color
        aw_settings = org.apple_wallet_settings or {}
        tier_color = tier_info.get('color') if (tier_info and tier_info.get('color')) else None
        bg_hex = tier_color or aw_settings.get('background_color') or org.brand_color or "#18181b"
        fg_hex = aw_settings.get('foreground_color') or "#ffffff"
        label_hex = aw_settings.get('label_color') or "#a1a1aa"

        background_color = hex_to_rgb(bg_hex, "rgb(24, 24, 27)")
        foreground_color = hex_to_rgb(fg_hex, "rgb(255, 255, 255)")
        label_color = hex_to_rgb(label_hex, "rgb(161, 161, 170)")

        # Format balance
        balance_num = customer.loyalty_balance
        balance_str = str(int(balance_num)) if balance_num == int(balance_num) else f"{balance_num:.2f}"

        # Guest name
        guest_name = f"{customer.first_name} {customer.last_name}".strip() or "Гость"

        # Web service URL for PassKit dynamic updates (if domain configured)
        domain = getattr(settings, 'WEBHOOK_DOMAIN', '').rstrip('/')
        web_service_url = f"{domain}/api/loyalty/apple-wallet" if domain else None
        auth_token = self.get_auth_token(customer)

        # Build barcodes: Code128 (barcode) or QR code based on organization setting (default: barcode)
        barcode_type = aw_settings.get('barcode_type', 'barcode')
        if barcode_type == 'qr':
            primary_format = "PKBarcodeFormatQR"
            fallback_format = "PKBarcodeFormatCode128"
        else:
            primary_format = "PKBarcodeFormatCode128"
            fallback_format = "PKBarcodeFormatQR"

        barcode_dict = {
            "format": primary_format,
            "message": card_number,
            "messageEncoding": "iso-8859-1",
            "altText": card_number
        }
        barcodes_list = [
            barcode_dict,
            {
                "format": fallback_format,
                "message": card_number,
                "messageEncoding": "iso-8859-1",
                "altText": card_number
            }
        ]

        # Header field (Top right): ДЕҢГЕЙ: / Название программы лояльности из iiko card right-aligned
        header_fields = [
            {
                "key": "tier",
                "label": "ДЕҢГЕЙ:",
                "value": loyalty_program_name,
                "textAlignment": "PKTextAlignmentRight"
            }
        ]

        # Primary fields: Company name (in place of client name)
        company_name = getattr(org, 'name', '') or aw_settings.get('class_name', '')
        primary_fields = [
            {
                "key": "company",
                "label": "",
                "value": company_name
            }
        ]

        # Change message template for APNs pass updates
        lang = getattr(customer, 'language', 'ru') or 'ru'
        templates = aw_settings.get('push_templates', {})
        tpl = templates.get(lang) or templates.get('ru', {})
        change_msg = tpl.get('change_message') or "Баланс бонусов обновлен: %@ ₸"
        if '%@' not in change_msg:
            change_msg = f"{change_msg}: %@ ₸"

        # Secondary fields (On banner):
        # Left: КАРТА ИЕСІ (label on top) and Guest name (value below)
        # Right: БАЛАНС: (label on top) and Balance (value below, right-aligned)
        secondary_fields = [
            {
                "key": "guest",
                "label": "КАРТА ИЕСІ",
                "value": guest_name,
                "textAlignment": "PKTextAlignmentLeft"
            },
            {
                "key": "balance",
                "label": "БАЛАНС:",
                "value": f"{balance_str} ₸",
                "textAlignment": "PKTextAlignmentRight",
                "changeMessage": change_msg
            }
        ]

        auxiliary_fields = []

        # Back fields: Card number, phone, contacts, info, rules
        back_fields = [
            {
                "key": "card_number",
                "label": "НОМЕР КАРТЫ",
                "value": card_number
            }
        ]
        if customer.phone:
            back_fields.append({
                "key": "phone",
                "label": "ТЕЛЕФОН",
                "value": customer.phone
            })
        back_fields.extend([
            {
                "key": "org_info",
                "label": "О ЗАВЕДЕНИИ",
                "value": getattr(org, 'description', '') or f"Программа лояльности {org.name}"
            },
            {
                "key": "card_rules",
                "label": "ПРАВИЛА НАЧИСЛЕНИЯ",
                "value": "Предъявляйте эту карту при каждом визите для начисления и списания бонусных баллов."
            }
        ])
        if getattr(org, 'address', None):
            back_fields.append({
                "key": "address",
                "label": "АДРЕС",
                "value": org.address
            })
        if getattr(org, 'website_url', None):
            back_fields.append({
                "key": "website",
                "label": "ВЕБ-САЙТ",
                "value": org.website_url
            })
        if getattr(org, 'instagram_link', None):
            back_fields.append({
                "key": "instagram",
                "label": "INSTAGRAM",
                "value": org.instagram_link
            })
        if getattr(org, 'whatsapp_link', None):
            back_fields.append({
                "key": "whatsapp",
                "label": "WHATSAPP",
                "value": org.whatsapp_link
            })
        if getattr(org, 'tma_direct_link', None):
            back_fields.append({
                "key": "tma_link",
                "label": "TELEGRAM MINI APP",
                "value": org.tma_direct_link
            })

        # Check for active marketing / broadcast announcement message for this pass
        from django.core.cache import cache
        broadcast_msg = None
        try:
            broadcast_msg = cache.get(f"apple_wallet_broadcast_{customer.id}")
        except Exception:
            pass

        if not broadcast_msg:
            try:
                from apps.mailing.models import MailingTask
                latest_mail = MailingTask.objects.filter(
                    organization=org,
                    channel_type=MailingTask.CHANNEL_APPLE_WALLET,
                    status__in=[MailingTask.STATUS_IN_PROGRESS, MailingTask.STATUS_DONE]
                ).order_by('-scheduled_at').first()
                if latest_mail:
                    lang = getattr(customer, 'language', 'ru') or 'ru'
                    tpl = latest_mail.message_kz if lang == 'kz' else latest_mail.message_ru
                    cust_name = customer.first_name or ("Құрметті қонақ" if lang == 'kz' else "Гость")
                    broadcast_msg = tpl.replace('{{user_name}}', cust_name).strip()
            except Exception:
                broadcast_msg = None

        # Marketing / broadcast announcement field
        # Note: In Apple PassKit, changeMessage alerts are ONLY displayed if the field already existed
        # on the pass before the update. Hence broadcast_notice is always included.
        notice_value = broadcast_msg or "Актуальные акции и новости заведения"
        back_fields.insert(0, {
            "key": "broadcast_notice",
            "label": "НОВОСТИ И АКЦИИ",
            "value": notice_value,
            "changeMessage": "%@"
        })

        program_title = aw_settings.get('class_name') or org.name

        pass_data: Dict[str, Any] = {
            "formatVersion": 1,
            "passTypeIdentifier": pass_type_id,
            "serialNumber": serial_number,
            "teamIdentifier": team_id,
            "organizationName": org.name,
            "description": f"Карта лояльности {org.name}",
            "logoText": "",
            "backgroundColor": background_color,
            "foregroundColor": foreground_color,
            "labelColor": label_color,
            "barcodes": barcodes_list,
            "barcode": barcode_dict,
            "storeCard": {
                "headerFields": header_fields,
                "primaryFields": primary_fields,
                "secondaryFields": secondary_fields,
                "auxiliaryFields": auxiliary_fields,
                "backFields": back_fields
            }
        }

        # Geolocation points (up to 10 points for lock-screen display)
        raw_locations = aw_settings.get('locations', [])
        if raw_locations:
            locations_list = []
            for loc in raw_locations[:10]:
                try:
                    lat = float(loc.get('latitude'))
                    lng = float(loc.get('longitude'))
                    loc_item: Dict[str, Any] = {
                        "latitude": lat,
                        "longitude": lng,
                    }
                    rel_text = loc.get('relevant_text') or loc.get('name')
                    if rel_text:
                        loc_item["relevantText"] = str(rel_text)
                    locations_list.append(loc_item)
                except (ValueError, TypeError):
                    continue
            if locations_list:
                pass_data["locations"] = locations_list
                pass_data["maxDistance"] = 100

        if web_service_url:
            pass_data["webServiceURL"] = web_service_url
            pass_data["authenticationToken"] = auth_token

        return pass_data

    def get_pass_assets(self, org: Organization, customer: Optional[Customer] = None) -> Dict[str, bytes]:
        """
        Retrieves or generates image assets for the pass:
        icon.png, icon@2x.png, logo.png, logo@2x.png, strip.png.
        Supports tier-specific strip banners with fallback to organization defaults.
        """
        assets: Dict[str, bytes] = {}

        # Parse brand color for fallback icons
        aw_settings = org.apple_wallet_settings or {}
        gw_settings = org.google_wallet_settings or {}

        tier_info = None
        if customer:
            tier_info = resolve_customer_tier(customer, org)

        tier_color = tier_info.get('color') if (tier_info and tier_info.get('color')) else None
        bg_hex = tier_color or aw_settings.get('background_color') or org.brand_color or "#18181b"
        s = bg_hex.strip().lstrip('#')
        r, g, b = 24, 24, 27
        if len(s) == 6:
            try:
                r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
            except ValueError:
                pass

        # Try to load custom logo bytes from media storage (Apple Wallet -> Google Wallet -> Branding)
        logo_url = aw_settings.get('logo_url') or gw_settings.get('logo_url') or (org.branding or {}).get('logo_url')
        custom_logo_bytes = None
        if logo_url:
            clean_path = logo_url.replace('/media/', '', 1).lstrip('/')
            try:
                if default_storage.exists(clean_path):
                    with default_storage.open(clean_path, 'rb') as f:
                        custom_logo_bytes = f.read()
            except Exception as e:
                logger.warning(f"Could not load custom logo from {clean_path}: {e}")

        # Provide icon.png (29x29) and icon@2x.png (58x58)
        default_icon = generate_png_bytes(width=29, height=29, r=r, g=g, b=b)
        default_icon_2x = generate_png_bytes(width=58, height=58, r=r, g=g, b=b)
        assets["icon.png"] = custom_logo_bytes or default_icon
        assets["icon@2x.png"] = custom_logo_bytes or default_icon_2x

        # Provide logo.png and logo@2x.png
        default_logo = generate_png_bytes(width=160, height=50, r=r, g=g, b=b, a=0)
        default_logo_2x = generate_png_bytes(width=320, height=100, r=r, g=g, b=b, a=0)
        assets["logo.png"] = custom_logo_bytes or default_logo
        assets["logo@2x.png"] = custom_logo_bytes or default_logo_2x

        # Provide strip banner: tier banner has priority over organization default
        strip_url = None
        if tier_info:
            strip_url = tier_info.get('banner_url')

        if not strip_url:
            strip_url = aw_settings.get('strip_url') or gw_settings.get('hero_image_url')

        if strip_url:
            strip_path = strip_url.replace('/media/', '', 1).lstrip('/')
            try:
                if default_storage.exists(strip_path):
                    with default_storage.open(strip_path, 'rb') as f:
                        strip_bytes = f.read()
                        assets["strip.png"] = strip_bytes
                        assets["strip@2x.png"] = strip_bytes
            except Exception as e:
                logger.warning(f"Could not load strip banner from {strip_path}: {e}")

        return assets

    def sign_manifest(self, manifest_bytes: bytes) -> bytes:
        """
        Signs manifest.json with PKCS#7 / CMS using Pass Type ID certificate and Apple WWDR CA.
        If certificates are not yet configured (e.g. enrollment pending), writes a dummy signature
        to allow packaging and schema validation.
        """
        if not self.is_signing_configured:
            logger.info("Apple Wallet certificates not configured. Using placeholder signature.")
            return b"DUMMY_PKCS7_SIGNATURE_PENDING_APPLE_CERTIFICATE"

        try:
            from cryptography import x509
            from cryptography.hazmat.primitives import serialization, hashes
            from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12

            signer_cert = None
            private_key = None

            # 1. Load from PKCS#12 (.p12) if provided
            if self.p12_data:
                password = self.key_password.encode('utf-8') if self.key_password else None
                try:
                    private_key, signer_cert, _ = pkcs12.load_key_and_certificates(self.p12_data, password=password)
                except Exception as ex_p12:
                    logger.warning(f"Failed to load p12 data: {ex_p12}")

            # 2. Otherwise load separate cert and key
            if not signer_cert and self.cert_pem:
                try:
                    signer_cert = x509.load_pem_x509_certificate(self.cert_pem)
                except Exception:
                    try:
                        signer_cert = x509.load_der_x509_certificate(self.cert_pem)
                    except Exception as ex_cert:
                        logger.warning(f"Failed to load certificate: {ex_cert}")

            if not private_key and self.key_pem:
                password = self.key_password.encode('utf-8') if self.key_password else None
                try:
                    private_key = serialization.load_pem_private_key(self.key_pem, password=password)
                except Exception as ex_key:
                    logger.warning(f"Failed to load private key: {ex_key}")

            if not signer_cert or not private_key:
                logger.error("Could not obtain both signer certificate and private key for Apple Wallet pass.")
                raise RuntimeError("Apple Wallet pass signing failed: missing signer certificate or private key.")

            builder = (
                pkcs7.PKCS7SignatureBuilder()
                .set_data(manifest_bytes)
                .add_signer(signer_cert, private_key, hashes.SHA256())
            )

            if self.wwdr_pem:
                try:
                    wwdr_cert = x509.load_pem_x509_certificate(self.wwdr_pem)
                except Exception:
                    try:
                        wwdr_cert = x509.load_der_x509_certificate(self.wwdr_pem)
                    except Exception as e:
                        wwdr_cert = None
                        logger.warning(f"Failed to attach WWDR CA certificate: {e}")
                if wwdr_cert:
                    builder = builder.add_certificate(wwdr_cert)

            signature_der = builder.sign(
                serialization.Encoding.DER,
                [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.Binary]
            )
            return signature_der

        except Exception as e:
            logger.error(f"Failed to sign Apple Wallet pass with PKCS#7: {e}")
            raise RuntimeError(f"Apple Wallet PKCS#7 signing failed: {e}")

    def create_pkpass(self, customer: Customer) -> io.BytesIO:
        """
        Builds, signs, and packages the complete .pkpass ZIP bundle in memory.
        Returns a BytesIO stream ready to be sent as an HTTP response.
        """
        pass_data = self.build_pass_json(customer)
        pass_json_bytes = json.dumps(pass_data, ensure_ascii=False, indent=2).encode('utf-8')

        assets = self.get_pass_assets(customer.organization, customer=customer)
        files_to_hash: Dict[str, bytes] = {
            "pass.json": pass_json_bytes,
            **assets
        }

        # Generate manifest.json (SHA-1 checksums)
        manifest: Dict[str, str] = {}
        for filename, data in files_to_hash.items():
            manifest[filename] = hashlib.sha1(data).hexdigest()

        manifest_bytes = json.dumps(manifest, indent=2).encode('utf-8')

        # Sign manifest
        signature_bytes = self.sign_manifest(manifest_bytes)

        # Create .pkpass ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as pkpass:
            for filename, data in files_to_hash.items():
                pkpass.writestr(filename, data)
            pkpass.writestr("manifest.json", manifest_bytes)
            pkpass.writestr("signature", signature_bytes)

        zip_buffer.seek(0)
        return zip_buffer

    def get_pass_download_url(self, customer: Customer) -> str:
        """
        Generates a secure, signed URL for downloading the .pkpass file.
        Accessible by Safari or TMA without requiring separate cookie auth.
        """
        token = signing.dumps(
            {"customer_id": customer.id, "org_id": customer.organization_id},
            salt="apple-wallet-pass"
        )
        domain = getattr(settings, 'WEBHOOK_DOMAIN', '').rstrip('/')
        path = f"/api/loyalty/public/passes/{token}/card.pkpass"
        return f"{domain}{path}" if domain else path
