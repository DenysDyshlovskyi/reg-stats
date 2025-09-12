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

# Define debug status and function
DEBUG = True
def print_debug(text):
    if DEBUG:
        print(text)

# Adds a client to online list
@database_sync_to_async
def add_to_online_list(client_id):
    from .models import ClientConnectionStatus, Clients
    if not Clients.objects.filter(id=client_id).exists():
        print_debug(f"Client {client_id} doesnt exist")
        return

    client = Clients.objects.get(id=client_id)
    if not ClientConnectionStatus.objects.filter(client_id=client_id).exists():
        ClientConnectionStatus(
            client_id=client,
            status=True
        ).save()
        print_debug(f"Client {client_id} added to online list")
    else:
        connection_row = ClientConnectionStatus.objects.get(client_id=client)
        connection_row.status = True
        connection_row.unix_timestamp = math.floor(time.time())
        connection_row.save()
        print_debug(f"Client {client_id} marked as online")

# Removes a client from online list
@database_sync_to_async
def remove_from_online_list(client_id):
    from .models import ClientConnectionStatus, Clients
    if not Clients.objects.filter(id=client_id).exists():
        print_debug(f"Client {client_id} doesnt exist")
        return

    client = Clients.objects.get(id=client_id)
    if ClientConnectionStatus.objects.filter(client_id=client_id).exists():
        connection_row = ClientConnectionStatus.objects.get(client_id=client)
        connection_row.status = False
        connection_row.save()
        print_debug(f"Client {client_id} marked as offline")
    else:
        ClientConnectionStatus(
            client_id=client,
            unix_timestamp = math.floor(time.time())
        ).save()
        print_debug(f"Client {client_id} marked as offline")


# Consumer client connects to
class ClientConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get client id and master key from session
        session = self.scope["session"]
        self.client_id = session.get("client_id")
        self.master_key = session.get("master_key")

        # Get ip address
        self.ip_address = self.scope.get("client")[0] if self.scope.get("client") else "Unavailable"

        print_debug(f"Client connected: ID: {self.client_id}, IP: {self.ip_address}, Master key: {self.master_key}")

        # Check if master key matches
        if self.master_key != settings.MASTER_KEY:
            await self.close(code=4000)
            return

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

        # Add client to online list
        await add_to_online_list(self.client_id)

        await self.accept()

    async def disconnect(self, code):
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

        # Remove client from online list
        await remove_from_online_list(self.client_id)
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