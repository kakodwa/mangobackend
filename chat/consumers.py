import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"🔥 WEBSOCKET CONNECTED: Room {self.room_id}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"⚠️ WEBSOCKET DISCONNECTED: Room {self.room_id} Code: {close_code}")

    async def receive(self, text_data):
        print(f"📥 WEBSOCKET RECEIVED PAYLOAD: {text_data}")
        try:
            data = json.loads(text_data)
            text_content = data.get('text') or data.get('message') or ''
            sender_id = data.get('sender_id')

            if not text_content.strip() or not sender_id:
                print(f"❌ INVALID PAYLOAD MISSING TEXT OR SENDER_ID: {data}")
                return

            # Save message to DB asynchronously
            msg = await self.save_message(sender_id, text_content)
            print(f"💾 MESSAGE SAVED TO DATABASE: ID {msg.id}")

            # Broadcast message payload to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'id': msg.id,
                    'room_id': int(self.room_id),
                    'sender_id': int(sender_id),
                    'text': msg.text,
                    'created_at': msg.created_at.isoformat(),
                }
            )
        except Exception as e:
            print(f"💥 ERROR IN CONSUMER RECEIVE: {e}")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, sender_id, text_content):
        room = ChatRoom.objects.get(id=self.room_id)
        sender = User.objects.get(id=sender_id)
        room.save() # Update updated_at timestamp on ChatRoom
        
        return ChatMessage.objects.create(
            room=room, 
            sender=sender, 
            text=text_content
        )