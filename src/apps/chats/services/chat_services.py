import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.chats.models import Conversation
from apps.chats.repositories.inter import IMessageRepo
from apps.chats.exceptions import MessageValidationError, MessageStorageError, MessageRetrievalError

logger = logging.getLogger(__name__)
MyUser = get_user_model()

class ChatService:
    def __init__(self, user_repo: MyUser.objects, conversation_repo: Conversation.objects, redis_repo: IMessageRepo, db_repo: IMessageRepo):
        self.user_repo = user_repo
        self.conversation_repo = conversation_repo
        self.redis_repo = redis_repo
        self.db_repo = db_repo

    def create_conversation(self, user_ids: list) -> str:
        try:
            participants = self.user_repo.objects.filter(id__in=user_ids)
            if not participants:
                raise ValidationError("No valid participants")
            conv = self.conversation_repo.objects.create()
            conv.participants.add(*participants)
            logger.info(f"Conversation created: {conv.id}")
            return str(conv.id)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise

    def send_message(self, conv_id: str, sender_id: int, text: str):
        try:
            message = {
                'sender': sender_id,
                'text': text,
                'timestamp': datetime.now().isoformat()
            }
            self.redis_repo.push_message(conv_id, message)
            self.db_repo.push_message(conv_id, message)
            logger.info(f"Message sent to conversation {conv_id}")
        except (MessageValidationError, MessageStorageError) as e:
            logger.error(f"Storage error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            raise

    def get_messages_from_redis(self, conv_id: str) -> list:
        try:
            messages = self.redis_repo.get_messages(conv_id)
            logger.info(f"Messages retrieved from Redis: {conv_id}")
            return messages
        except MessageRetrievalError as e:
            logger.error(f"Retrieval error from Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving messages from Redis: {e}")
            raise

    def get_messages_from_db(self, conv_id: str) -> list:
        try:
            messages = self.db_repo.get_messages(conv_id)
            for msg in messages:
                self.redis_repo.push_message(conv_id, msg)
            logger.info(f"Messages retrieved from database and cached in Redis: {conv_id}")
            return messages
        except MessageRetrievalError as e:
            logger.error(f"Retrieval error from database: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving messages from database: {e}")
            raise