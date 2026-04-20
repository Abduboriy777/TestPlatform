import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, ChatMessage, RoomMembership


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"chat_room_{self.room_id}"

        if not self.user.is_authenticated:
            await self.close()
            return

        allowed = await self.user_in_room(self.user.id, self.room_id)
        if not allowed:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        message = (data.get("message") or "").strip()
        if not message:
            return

        saved = await self.save_message(self.room_id, self.user.id, message)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "message": saved["message"],
                "sender": saved["sender"],
                "sender_id": saved["sender_id"],
                "time": saved["time"],
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def user_in_room(self, user_id, room_id):
        return RoomMembership.objects.filter(room_id=room_id, user_id=user_id).exists()

    @database_sync_to_async
    def save_message(self, room_id, user_id, text):
        room = ChatRoom.objects.get(id=room_id)
        msg = ChatMessage.objects.create(room=room, sender_id=user_id, text=text)
        return {
            "message": msg.text,
            "sender": msg.sender.username,
            "sender_id": msg.sender_id,
            "time": msg.created_at.strftime("%H:%M"),
        }