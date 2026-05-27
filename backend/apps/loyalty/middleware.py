from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from apps.loyalty.models import Customer
from urllib.parse import parse_qs

@database_sync_to_async
def get_customer_from_token(token_string):
    try:
        token = AccessToken(token_string)
        user_type = token.get("user_type")
        user_id = token.get("user_id")
        if user_type == "customer":
            return Customer.objects.get(pk=user_id)
    except Exception:
        pass
    return None

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]
        
        scope["user"] = None
        if token:
            scope["user"] = await get_customer_from_token(token)
            
        return await super().__call__(scope, receive, send)
