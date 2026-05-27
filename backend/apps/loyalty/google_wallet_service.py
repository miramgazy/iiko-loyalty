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
            "hexBackgroundColor": class_data.get('hex_background_color', '#000000'),
        }
        
        if class_data.get('logo_url'):
            payload["programLogo"] = {
                "sourceUri": {
                    "uri": class_data.get('logo_url')
                }
            }

        if class_data.get('hero_image_url'):
            payload["heroImage"] = {
                "sourceUri": {
                    "uri": class_data.get('hero_image_url')
                }
            }

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
        org = customer.organization
        if not org.google_issuer_id or not org.google_loyalty_class_id:
            raise ValueError("Organization is not fully configured for Google Wallet")

        # Object ID format: issuer_id.object_suffix
        object_id = customer.google_wallet_object_id
        if not object_id:
            object_id = f"{org.google_issuer_id}.cust_{customer.id}"
            customer.google_wallet_object_id = object_id
            customer.save(update_fields=['google_wallet_object_id'])
            
        barcode_value = customer.wallet_barcode

        # Build LoyaltyObject
        loyalty_object = {
            "id": object_id,
            "classId": org.google_loyalty_class_id,
            "state": "ACTIVE",
            "accountId": str(customer.id),
            "accountName": f"{customer.first_name} {customer.last_name}".strip() or "Гость",
            "barcode": {
                "type": "qrCode",
                "value": barcode_value,
                "alternateText": barcode_value
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
