from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from .models import Order

class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope['url_route']['kwargs']['order_id']
        self.order_group_name = f'order_{self.order_id}'

        # Join order group
        await self.channel_layer.group_add(
            self.order_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave order group
        await self.channel_layer.group_discard(
            self.order_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'status_update':
            await self.update_order_status(data)

    async def order_status_message(self, event):
        # Send status update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'message': event.get('message', ''),
        }))

    @database_sync_to_async
    def update_order_status(self, data):
        try:
            order = Order.objects.get(id=self.order_id)
            order.status = data.get('status', order.status)
            order.save()
        except Order.DoesNotExist:
            pass
