"""
Routing configuration for WebSocket connections in the kitchen app.
"""
from django.urls import re_path
from .consumers import OrdersConsumer

websocket_urlpatterns = [
    re_path(r'^ws/orders/?$', OrdersConsumer.as_asgi()),
]
