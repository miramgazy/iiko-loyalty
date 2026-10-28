import base64
import json
import jwt
import requests
import os
from django.conf import settings
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from apps.loyalty.models import Customer
from apps.core.models import Organization

class GoogleWalletService:
    def __init__(self):
        # Read from environment
        b64_creds = os.environ.get('GOOGLE_WALLET_CREDENTIALS_BASE64')
        if not b64_creds:
            raise ValueError("GOOGLE_WALLET_CREDENTIALS_BASE64 not set in environment.")
        
        creds_json = base64.b64decode(b64_creds).decode('utf-8')
        self.credentials_dict = json.loads(creds_json)
        self.client_email = self.credentials_dict['client_email']
        self.private_key = self.credentials_dict['private_key']
        
        self.scopes = ["https://www.googleapis.com/auth/wallet_object.issuer"]
        self.credentials = service_account.Credentials.from_service_account_info(
            self.credentials_dict, scopes=self.scopes
        )
        self.base_url = "https://walletobjects.googleapis.com/walletobjects/v1"

    def get_access_token(self):
        req = Request()
        self.credentials.refresh(req)
        return self.credentials.token

    def create_or_update_loyalty_class(self, organization: Organization, class_data: dict):
        """
        class_data contains:
        - class_name (str)
        - logo_url (str)
        - hero_image_url (str, optional)
        - hex_background_color (str)
        - issuer_name (str)
        """
        if not organization.google_issuer_id:
            raise ValueError("Organization google_issuer_id is not set.")
        
        class_id = f"{organization.google_issuer_id}.{organization.slug}_loyalty"
        
        payload = {
            "id": class_id,
            "classTemplateInfo": {
                "cardTemplateOverride": {
                    "cardRowTemplateInfos": [
                        {
                            "twoItems": {
                                "startItem": {
                                    "firstValue": {
                                        "fields": [
                                            {
                                                "fieldPath": "object.textModulesData['balance']"
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            },
            "issuerName": class_data.get('issuer_name', organization.name),
            "programName": class_data.get('class_name', organization.name),
            "reviewStatus": "UNDER_REVIEW",
            "hexBackgroundColor": class_data.get('hex_background_color') or organization.brand_color or '#000000',
        }
        
        logo_url = class_data.get('logo_url')
        if logo_url:
            if logo_url.startswith('/'):
                from django.conf import settings
                domain = getattr(settings, 'WEBHOOK_DOMAIN', '').rstrip('/')
                logo_url = f"{domain}{logo_url}"
            payload["programLogo"] = {
                "sourceUri": {
                    "uri": logo_url
                }
            }

        hero_image_url = class_data.get('hero_image_url')
        if hero_image_url:
            if hero_image_url.startswith('/'):
                from django.conf import settings
                domain = getattr(settings, 'WEBHOOK_DOMAIN', '').rstrip('/')
                hero_image_url = f"{domain}{hero_image_url}"
            payload["heroImage"] = {
                "sourceUri": {
                    "uri": hero_image_url
                }
            }

        # Geolocation points (up to 10 locations)
        locations = class_data.get('locations')
        if locations is None and organization.google_wallet_settings:
            locations = organization.google_wallet_settings.get('locations', [])
        
        if locations and isinstance(locations, list):
            valid_locs = []
            for loc in locations[:10]:
                if not isinstance(loc, dict):
                    continue
                try:
                    lat = float(loc.get('latitude', 0))
                    lng = float(loc.get('longitude', 0))
                    if -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0 and (lat != 0 or lng != 0):
                        valid_locs.append({
                            "latitude": lat,
                            "longitude": lng,
                        })
                except (ValueError, TypeError):
                    continue
            if valid_locs:
                payload["locations"] = valid_locs

        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Check if class exists
        get_url = f"{self.base_url}/loyaltyClass/{class_id}"
        resp = requests.get(get_url, headers=headers)
        
        if resp.status_code == 200:
            # Update
            put_url = f"{self.base_url}/loyaltyClass/{class_id}"
            res = requests.put(put_url, headers=headers, json=payload)
            res.raise_for_status()
        else:
            # Create
            post_url = f"{self.base_url}/loyaltyClass"
            res = requests.post(post_url, headers=headers, json=payload)
            res.raise_for_status()
            
        organization.google_loyalty_class_id = class_id
        organization.save(update_fields=['google_loyalty_class_id'])
        
        return res.json()

    def generate_google_wallet_link(self, customer: Customer, current_balance: str) -> str:
        import time
        org = customer.organization
        if not org.google_issuer_id or not org.google_loyalty_class_id:
            raise ValueError("Organization is not fully configured for Google Wallet")

        # Normalize class_id: ensure it has issuer_id prefix
        class_id = org.google_loyalty_class_id.strip()
        if not class_id.startswith(f"{org.google_issuer_id}."):
            class_id = f"{org.google_issuer_id}.{class_id}"

        # Object ID format: issuer_id.object_suffix
        object_id = customer.google_wallet_object_id
        update_customer_fields = []
        if not object_id:
            object_id = f"{org.google_issuer_id}.cust_{customer.id}"
            customer.google_wallet_object_id = object_id
            update_customer_fields.append('google_wallet_object_id')
        if customer.wallet_type != 'google':
            customer.wallet_type = 'google'
            update_customer_fields.append('wallet_type')
        if update_customer_fields:
            customer.save(update_fields=update_customer_fields)

        # Ensure customer has an iiko_card_number
        if not customer.iiko_card_number:
            from apps.loyalty.utils import generate_unique_card_number
            customer.iiko_card_number = generate_unique_card_number(org)
            customer.save(update_fields=['iiko_card_number'])

            # Send to iiko if customer is already created in iiko
            if customer.iiko_customer_id:
                try:
                    from apps.loyalty.services import IikoLoyaltyService
                    iiko_svc = IikoLoyaltyService(org)
                    iiko_svc.add_virtual_card(customer.iiko_customer_id, str(customer.iiko_card_number))
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not push card to iiko synchronously: {e}")
            elif customer.phone:
                from apps.loyalty.tasks import sync_customer_to_iiko
                sync_customer_to_iiko.delay(customer.id, push=True)

        barcode_value = str(customer.iiko_card_number or customer.wallet_barcode or customer.id)

        # Build LoyaltyObject
        loyalty_object = {
            "id": object_id,
            "classId": class_id,
            "state": "ACTIVE",
            "accountId": barcode_value,
            "accountName": f"{customer.first_name} {customer.last_name}".strip() or "Гость",
            "barcode": {
                "type": "QR_CODE",
                "value": barcode_value,
                "alternateText": barcode_value
            },
            "loyaltyPoints": {
                "label": "Бонусы",
                "balance": {
                    "string": current_balance
                }
            },
            "textModulesData": [
                {
                    "id": "balance",
                    "header": "Баланс бонусов",
                    "body": current_balance
                }
            ]
        }

        # Build JWT
        claims = {
            "iss": self.client_email,
            "aud": "google",
            "typ": "savetowallet",
            "iat": int(time.time()),
            "origins": [],
            "payload": {
                "loyaltyObjects": [loyalty_object]
            }
        }

        token = jwt.encode(claims, self.private_key, algorithm="RS256")
        
        # In newer versions of PyJWT, encode returns a string. In older ones, bytes.
        if isinstance(token, bytes):
            token = token.decode("utf-8")

        return f"https://pay.google.com/gp/v/save/{token}"

    def update_customer_balance(self, customer: Customer, current_balance: str = None) -> bool:
        """
        Updates the loyalty points and balance on the user's active Google Wallet pass via PATCH API.
        Returns True if successfully updated, False if pass not found or Google Wallet is not configured.
        """
        org = customer.organization
        if not org.is_google_wallet_enabled or not org.google_issuer_id:
            return False

        object_id = customer.google_wallet_object_id
        if not object_id:
            return False

        if current_balance is None:
            balance_num = customer.loyalty_balance
            balance_str = str(int(balance_num)) if balance_num == int(balance_num) else str(balance_num)
            current_balance = f"{balance_str} ₸"

        patch_payload = {
            "loyaltyPoints": {
                "label": "Бонусы",
                "balance": {
                    "string": current_balance
                }
            },
            "textModulesData": [
                {
                    "id": "balance",
                    "header": "Баланс бонусов",
                    "body": current_balance
                }
            ]
        }

        # Sync barcode to iiko_card_number if available
        if customer.iiko_card_number:
            card_num = str(customer.iiko_card_number)
            patch_payload["accountId"] = card_num
            patch_payload["barcode"] = {
                "type": "QR_CODE",
                "value": card_num,
                "alternateText": card_num
            }

        try:
            token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            patch_url = f"{self.base_url}/loyaltyObject/{object_id}"
            resp = requests.patch(patch_url, headers=headers, json=patch_payload, timeout=10)
            if resp.status_code == 200:
                return True
            elif resp.status_code == 404:
                # The user generated the link but hasn't actually saved the pass into Google Wallet yet
                return False
            else:
                resp.raise_for_status()
                return True
        except Exception as e:
            # Log error without breaking caller execution
            import logging
            logging.getLogger(__name__).warning(f"Google Wallet PATCH balance failed for customer {customer.id}: {e}")
            return False

    def send_push_message(self, customer: Customer, title: str, body: str, message_id: str = None) -> bool:
        """
        Sends a push notification message to the customer's Google Wallet pass via addMessage API.
        Enforces character limits according to Google Wallet specifications:
        - header: max 35 characters
        - body: max 200 characters
        """
        org = customer.organization
        if not org.is_google_wallet_enabled or not org.google_issuer_id:
            return False

        object_id = customer.google_wallet_object_id
        if not object_id:
            return False

        try:
            token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            url = f"{self.base_url}/loyaltyObject/{object_id}/addMessage"

            clean_title = (title or "Баланс бонусов обновлен").strip()[:35]
            clean_body = (body or f"Баланс: {customer.loyalty_balance}").strip()[:200]

            import time
            payload = {
                "message": {
                    "header": clean_title,
                    "body": clean_body,
                    "id": message_id or f"msg_{int(time.time())}_{customer.id}",
                    "messageType": "TEXT"
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code in (200, 201):
                return True
            else:
                import logging
                logging.getLogger(__name__).warning(
                    f"Google Wallet addMessage returned {resp.status_code} for customer {customer.id}: {resp.text}"
                )
                return False
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Google Wallet addMessage error for customer {customer.id}: {e}")
            return False

