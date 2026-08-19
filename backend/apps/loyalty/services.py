import httpx
from django.core.cache import cache
from apps.core.models import Organization
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class IikoAuthService:
    def __init__(self, organization: Organization):
        self.org = organization
        self.cache_key = f"iiko_token_{self.org.id}"

    def get_access_token(self) -> str:
        try:
            token = cache.get(self.cache_key)
            if token:
                return token
        except Exception:
            pass

        url = f"{self.org.iiko_api_base_url.rstrip('/')}/access_token"
        payload = {}
        if self.org.iiko_api_login:
            payload["apiLogin"] = self.org.iiko_api_login
            payload["apiKey"] = self.org.iiko_api_login
        if self.org.iiko_app_id:
            payload["appId"] = self.org.iiko_app_id
        if self.org.iiko_client_secret:
            payload["clientSecret"] = self.org.iiko_client_secret
        
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            
            token = response.json().get("token")
            if not token:
                raise ValueError("No token returned from iiko API")
            
            try:
                cache.set(self.cache_key, token, timeout=1500)
            except Exception:
                pass
            return token

class IikoServerAuthService:
    def __init__(self, organization: Organization):
        self.org = organization
        self.cache_key = f"iiko_server_token_{self.org.id}"

    def get_access_token(self) -> str:
        try:
            token = cache.get(self.cache_key)
            if token:
                return token
        except Exception:
            pass

        if not self.org.iiko_server_url:
            raise ValueError("Адрес iiko Server не настроен")
        if not self.org.iiko_server_login or not self.org.iiko_server_password:
            raise ValueError("Логин или пароль iiko Server не настроен")

        import hashlib
        password_hash = hashlib.sha1(self.org.iiko_server_password.encode('utf-8')).hexdigest()

        server_url = self.org.iiko_server_url.rstrip('/')
        url = f"{server_url}/resto/api/auth"
        params = {
            "login": self.org.iiko_server_login,
            "pass": password_hash
        }

        # Bypassing SSL verification for RMS servers with self-signed certs
        with httpx.Client(timeout=15, verify=False) as client:
            response = client.post(url, data=params)
            
            if response.status_code != 200:
                error_msg = response.text
                raise ValueError(f"Сервер вернул код {response.status_code}: {error_msg}")

            token = response.text.strip()
            if not token or len(token) < 10:
                raise ValueError(f"Сервер вернул некорректный токен: {token}")

            try:
                cache.set(self.cache_key, token, timeout=1800)
            except Exception:
                pass

            return token

    def logout(self) -> None:
        """
        Releases the license slot on the iiko Server.
        """
        try:
            token = cache.get(self.cache_key)
            if not token:
                return
        except Exception:
            return

        if not self.org.iiko_server_url:
            return

        server_url = self.org.iiko_server_url.rstrip('/')
        url = f"{server_url}/resto/api/logout"
        params = {"key": token}

        try:
            with httpx.Client(timeout=10, verify=False) as client:
                client.get(url, params=params)
        except Exception:
            pass
        finally:
            try:
                cache.delete(self.cache_key)
            except Exception:
                pass

class BaseIikoIntegrationService(ABC):
    def __init__(self, organization: Organization):
        self.org = organization
        self.auth_service = IikoAuthService(organization)

    def _get_headers(self) -> dict:
        token = self.auth_service.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    @abstractmethod
    def get_customer_info_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_customer_info_by_id(self, iiko_customer_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_or_update_customer(self, phone: str, first_name: str = "", last_name: str = "", email: str = "", birthday: str = None) -> str:
        pass

    @abstractmethod
    def get_customer_balance(self, iiko_customer_id: str) -> float:
        pass
        
    @abstractmethod
    def add_virtual_card(self, customer_id: str, card_number: str) -> None:
        pass


class IikoCloudIntegrationService(BaseIikoIntegrationService):
    def _get_api_v1_url(self, endpoint: str) -> str:
        base = self.org.iiko_api_base_url.rstrip('/')
        if '/api/v2' in base:
            base = base.replace('/api/v2', '/api/1')
        elif '/api/2' in base:
            base = base.replace('/api/2', '/api/1')
        return f"{base}{endpoint}"

    def get_customer_info_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        url = self._get_api_v1_url("/loyalty/iiko/customer/info")
        payload = {
            "organizationId": str(self.org.iiko_organization_id),
            "type": "phone",
            "phone": phone
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            if response.status_code == 404:
                return None
            if response.status_code == 400:
                try:
                    data = response.json()
                    if data.get("code") == "Transport_WrongCustomerNumber" or data.get("errorCode") == "Validation_IncorrectPhone":
                        return None
                except Exception:
                    pass
            response.raise_for_status()
            return response.json()
            
    def get_customer_info_by_id(self, iiko_customer_id: str) -> Optional[Dict[str, Any]]:
        url = self._get_api_v1_url("/loyalty/iiko/customer/info")
        payload = {
            "organizationId": str(self.org.iiko_organization_id),
            "type": "id",
            "id": str(iiko_customer_id)
        }
        
        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            if response.status_code == 404:
                return None
            if response.status_code == 400:
                try:
                    data = response.json()
                    if data.get("code") == "Transport_WrongCustomerId" or data.get("errorCode") == "Customer_CustomerNotFound":
                        return None
                except Exception:
                    pass
            response.raise_for_status()
            return response.json()

    def create_or_update_customer(self, phone: str, first_name: str = "", last_name: str = "", email: str = "", birthday: str = None) -> str:
        url = self._get_api_v1_url("/loyalty/iiko/customer/create_or_update")
        
        payload = {
            "organizationId": str(self.org.iiko_organization_id),
            "phone": phone,
            "name": first_name or "Guest",
            "consentStatus": 1
        }
        if last_name:
            payload["surname"] = last_name
        if email:
            payload["email"] = email
        if birthday:
            if len(birthday) == 10:
                payload["birthday"] = f"{birthday}T00:00:00Z"
            else:
                payload["birthday"] = birthday

        if self.org.iiko_loyalty_program_id:
            payload["loyaltyProgramId"] = str(self.org.iiko_loyalty_program_id)

        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            customer_data = response.json()
            return customer_data.get("id")

    def add_virtual_card(self, customer_id: str, card_number: str) -> None:
        url = self._get_api_v1_url("/loyalty/iiko/customer/card/add")
        
        payload = {
            "organizationId": str(self.org.iiko_organization_id),
            "customerId": str(customer_id),
            "cardNumber": str(card_number),
            "cardTrack": str(card_number)
        }

        with httpx.Client(timeout=10) as client:
            response = client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()

    def get_customer_balance(self, iiko_customer_id: str) -> float:
        customer_data = self.get_customer_info_by_id(iiko_customer_id)
        if not customer_data:
            return 0.0
            
        wallet_balances = customer_data.get("walletBalances", [])
        total_balance = 0.0
        for wallet in wallet_balances:
            if wallet.get("type") == 1:
                total_balance += float(wallet.get("balance", 0))
        return total_balance

class IikoCardIntegrationService(BaseIikoIntegrationService):
    """Legacy iikoCard API implementation placeholder."""
    def get_customer_info_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Legacy iikoCard integration not fully implemented")
        
    def get_customer_info_by_id(self, iiko_customer_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Legacy iikoCard integration not fully implemented")

    def create_or_update_customer(self, phone: str, first_name: str = "", last_name: str = "", email: str = "", birthday: str = None) -> str:
        raise NotImplementedError("Legacy iikoCard integration not fully implemented")

    def get_customer_balance(self, iiko_customer_id: str) -> float:
        raise NotImplementedError("Legacy iikoCard integration not fully implemented")
        
    def add_virtual_card(self, customer_id: str, card_number: str) -> None:
        raise NotImplementedError("Legacy iikoCard integration not fully implemented")

def get_iiko_service(organization: Organization) -> BaseIikoIntegrationService:
    if organization.iiko_integration_type == 'iiko_card':
        return IikoCardIntegrationService(organization)
    return IikoCloudIntegrationService(organization)

IikoLoyaltyService = get_iiko_service
