from typing import Dict, List
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from apps.chats.exceptions import MessageStorageError, MessageRetrievalError
from apps.chats.models import Conversation, Message
from apps.chats.repositories.inter import IMessageRepo, IConsumerRepo
from apps.chats.validators import validate_message_required_field
from loggers import get_django_logger

logger = get_django_logger()
MyUser = get_user_model()

class DatabaseMessageRepo(IMessageRepo):
    def push_message(self, conv_id: str, message: Dict) -> None:
        try:
            if not validate_message_required_field(message):
                raise ValueError("The message must contain sender, text, timestamp")

            conversation = Conversation.objects.get(id=conv_id)
            sender = MyUser.objects.get(id=message['sender'])
            Message.objects.create(
                conversation=conversation,
                sender=sender,
                text=message['text'],
                timestamp=message['timestamp']
            )
            logger.info(f"Message saved in the database: {conv_id}")
        except ObjectDoesNotExist as e:
            logger.error(f"Conversation or user not found: {e}")
            raise MessageStorageError(e)
        except Exception as e:
            logger.error(f"Error saving to the database: {e}")
            raise MessageStorageError(e)

    def get_messages(self, conv_id: str) -> List[Dict]:
        try:
            messages = Message.objects.filter(conversation__id=conv_id).order_by('timestamp')
            return [
                {
                    'sender': m.sender.id,
                    'text': m.text,
                    'timestamp': m.timestamp.isoformat()
                } for m in messages
            ]
        except Exception as e:
            logger.error(f"Error retrieving from database: {e}")
            raise MessageRetrievalError(e)
