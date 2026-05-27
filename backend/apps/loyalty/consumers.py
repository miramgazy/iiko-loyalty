from channels.generic.websocket import AsyncJsonWebsocketConsumer

class LoyaltyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        try:
            self.customer_id = int(self.scope['url_route']['kwargs']['customer_id'])
        except (ValueError, KeyError):
            await self.close()
            return

        customer = self.scope.get('user')
        
        if not customer or customer.id != self.customer_id:
            await self.close()
            return
            
        self.group_name = f"user_{self.customer_id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def user_update(self, event):
        # Format required: {"type": "user_update", "message": {"event": "phone_updated", "phone": "+7..."}}
        await self.send_json(event)
