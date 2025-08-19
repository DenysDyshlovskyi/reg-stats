# WebSocket patterns are stored here

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/client/", consumers.ClientConsumer.as_asgi())
]