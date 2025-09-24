import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chats.consumers.config import chat_service
from apps.chats.utils import create_conversation_status_message


class ConversationConsumer(AsyncWebsocketConsumer):
    group_name = "conversations"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_conversations()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_conversations(self, event=None):
        try:
            conversations = await database_sync_to_async(chat_service.get_all_conversations)()
            await self.send(text_data=json.dumps({'conversations': conversations}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error retrieving conversations: {str(e)}'}))

    async def add_conversation(self, event):
        await self.send(text_data=json.dumps(create_conversation_status_message(event['id'], 'joined')))

    async def remove_conversation(self, event):
        await self.send(text_data=json.dumps(create_conversation_status_message(event['id'], 'left')))