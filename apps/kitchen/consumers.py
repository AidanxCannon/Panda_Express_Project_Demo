"""Defines the asynchronous consumers for the kitchen app."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class OrdersConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time order and inventory updates in the kitchen app.
    Agnostic to both order and inventory updates, differentiating based on message type.
    """
    async def connect(self):
        """
        connect to WebSocket, adding to 'orders' and 'inventory' groups.
        """
        await self.channel_layer.group_add('orders', self.channel_name)
        await self.channel_layer.group_add('inventory', self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        """Disconnect from WebSocket, removing from 'orders' and 'inventory' groups."""
        await self.channel_layer.group_discard('orders', self.channel_name)
        await self.channel_layer.group_discard('inventory', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Receive message from WebSocket client."""
        # Optional: ignore empty client messages to avoid blank orders
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'type': 'error', 'error': 'invalid json'}))
            return
        # Do not echo back unless explicitly an order
        if data.get('type') == 'order':
            await self.channel_layer.group_send('orders', {
                'type': 'order.update',
                'message': data,
            })

    async def order_update(self, event):
        """send order update to WebSocket client."""
        await self.send(text_data=json.dumps(event.get('message', {})))
    
    async def inventory_update(self, event):
        """send inventory update to WebSocket client."""
        await self.send(text_data=json.dumps(event.get('message', {})))
