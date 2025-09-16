from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import os
import django
import json
import time
import math
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "regstats.settings")
from django.conf import settings
django.setup()
from regstats_server.models import Clients

# Define debug status and function
DEBUG = True
def print_debug(text):
    if DEBUG:
        print(text)

@database_sync_to_async
def check_client_id(client_id):
    if not Clients.objects.get(id=client_id):
        return False
    else:
        return True

# Consumer client connects to
class ClientConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get client id and master key from session
        session = self.scope["session"]
        self.client_id = session.get("client_id")
        self.master_key = session.get("master_key")

        if not self.client_id or not self.master_key:
            await self.close(code=4000)
            return
        
        # Check if client exists
        result = await check_client_id(self.client_id)
        if not result:
            await self.close(code=4000)
            return

        # Check if master key matches
        if self.master_key != settings.MASTER_KEY:
            await self.close(code=4000)
            return

        # Get ip address
        self.ip_address = self.scope.get("client")[0] if self.scope.get("client") else "Unavailable"

        print_debug(f"Client connected: ID: {self.client_id}, IP: {self.ip_address}, Master key: {self.master_key}")

        # Join group with other clients
        self.group_name = "client_group"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Send message that you connected
        await self.channel_layer.group_send(
            self.group_name, {
                'type': 'ws.message',
                'message': {
                    'sender': 'c',
                    'type': 'connect',
                    'client_id': self.client_id
                }
            }
        )

        await self.accept()

    async def disconnect(self, code):
        if self.client_id and self.ip_address and self.master_key:
            print_debug(f"Client disconnected: ID: {self.client_id}, IP: {self.ip_address}, Master key: {self.master_key}")
            # Send message that you disconnected
            await self.channel_layer.group_send(
                self.group_name, {
                    'type': 'ws.message',
                    'message': {
                        'sender': 'c',
                        'type': 'disconnect',
                        'client_id': self.client_id
                    }
                }
            )

        pass

    async def receive(self, text_data):
        print_debug(f"Client consumer received data: {text_data}")
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'ws.message',
                'message': text_data
            }
        )

    async def ws_message(self, event):
        print_debug(f"Client consumer received data event: {event}")
        message = event['message']
        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps({
            'message': message
        }))

# Consumer browser connects to
class BrowserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get ip address
        self.ip_address = self.scope.get("client")[0] if self.scope.get("client") else "Unavailable"

        print_debug(f"Browser connected: IP: {self.ip_address}")

        # Join group with clients
        self.group_name = "client_group"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, code):
        print_debug(f"Browser disconnected: IP: {self.ip_address}")
        pass

    async def receive(self, text_data):
        print_debug(f"Browser consumer received data: {text_data}")
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'ws.message',
                'message': text_data
            }
        )

    async def ws_message(self, event):
        print_debug(f"Browser consumer received data event: {event}")
        message = event['message']
        # Send the message to the WebSocket client
        await self.send(text_data=json.dumps({
            'message': message
        }))