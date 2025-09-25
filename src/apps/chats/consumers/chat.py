import json
from datetime import datetime

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chats.consumers.config import chat_service
from apps.chats.exceptions import ConversationNotFoundError
from apps.chats.utils import create_user_status_message
from apps.users.serializers import MyUserSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conv_id = self.scope['url_route']['kwargs']['conv_id']
        self.conv_group_name = f'chat_{self.conv_id}'

        try:
            await self.check_conversation_exists()
        except ConversationNotFoundError as e:
            await self.close(code=404, reason=str(e))
            return
        except Exception as e:
            await self.close(code=500, reason=f"Unexpected error: {str(e)}")
            return

        await self.channel_layer.group_add(self.conv_group_name, self.channel_name)
        await self.accept()


        await self.channel_layer.group_send(
            self.conv_group_name,
            create_user_status_message(self.scope['user'], 'joined')
        )

        await self.add_users()
        await self.send_users()
        await self.send_history()


    async def disconnect(self, close_code):
        if self.conv_group_name:
            await self.channel_layer.group_send(
                self.conv_group_name,
                create_user_status_message(self.scope['user'], 'left')
            )
            await self.channel_layer.group_discard(self.conv_group_name, self.channel_name)
            await self.remove_user()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            text = data.get('text')

            if not text:
                await self.send(text_data=json.dumps({'error': 'Message text is required'}))
                return

            sender_id = self.scope['user'].id
            message = {
                'type': 'message',
                'sender': sender_id,
                'text': text,
                'timestamp': datetime.now().isoformat(),
                'user': MyUserSerializer(self.scope['user']).data
            }

            await database_sync_to_async(chat_service.send_message)(
                conv_id=self.conv_id,
                sender_id=sender_id,
                text=text
            )

            await self.channel_layer.group_send(
                self.conv_group_name,
                {
                    'type': 'chat_message',
                    'message': message
                }
            )
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON format'}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error processing message: {str(e)}'}))

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'status': event['status'],
            'timestamp': event['timestamp'],
            'user': event['user']
        }))

    @database_sync_to_async
    def check_conversation_exists(self):
        return chat_service.conversation_exists(self.conv_id)

    async def send_history(self):
        try:
            # messages = await database_sync_to_async(chat_service.get_messages_from_redis)(self.conv_id)
            # if not messages:
            messages = await database_sync_to_async(chat_service.get_messages_from_db)(self.conv_id)
            await self.send(text_data=json.dumps({'type': 'history', 'messages': messages}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error retrieving history: {str(e)}'}))

    async def send_users(self):
        try:
            users = await database_sync_to_async(chat_service.get_active_users)(self.conv_id)
            serialized_users = MyUserSerializer(users, many=True).data
            await self.send(text_data=json.dumps({'type':'user_list','users': serialized_users}))
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error retrieving users: {str(e)}'}))

    async def add_users(self):
        try:
            await database_sync_to_async(chat_service.add_active_user)(self.conv_id, self.scope['user'].id)
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error adding users: {str(e)}'}))

    async def remove_user(self):
        try:
            await database_sync_to_async(chat_service.remove_active_user)(self.conv_id, self.scope['user'].id)
        except Exception as e:
            await self.send(text_data=json.dumps({'error': f'Error removing users: {str(e)}'}))