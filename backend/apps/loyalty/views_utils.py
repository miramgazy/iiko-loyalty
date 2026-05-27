import hmac
import hashlib
import json
import urllib.parse
from datetime import datetime, timezone
from rest_framework_simplejwt.tokens import RefreshToken

def validate_tg_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validates Telegram initData signature and returns user dictionary.
    Raises ValueError on invalid signature or if token is older than 24 hours.
    """
    params = dict(urllib.parse.parse_qsl(init_data))
    if 'hash' not in params:
        raise ValueError("Missing hash in initData")
    
    received_hash = params.pop('hash')
    
    sorted_params = sorted(params.items())
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_params])
    
    secret_key = hmac.new(b"WebAppData", bot_token.encode('utf-8'), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid hash signature")
        
    auth_date_str = params.get('auth_date')
    if not auth_date_str:
        raise ValueError("Missing auth_date in initData")
    try:
        auth_date = int(auth_date_str)
        now = datetime.now(timezone.utc).timestamp()
        if now - auth_date > 86400:
            raise ValueError("initData signature expired")
    except ValueError:
        raise ValueError("Invalid auth_date format")
        
    user_str = params.get('user')
    if not user_str:
        raise ValueError("Missing user field in initData")
        
    try:
        user_data = json.loads(user_str)
        return user_data
    except Exception:
        raise ValueError("Invalid user JSON in initData")

def get_tokens_for_customer(customer) -> dict:
    """
    Generates SimpleJWT access/refresh pair with user_type='customer' payload claim.
    """
    refresh = RefreshToken()
    refresh['user_id'] = customer.id
    refresh['user_type'] = 'customer'
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
