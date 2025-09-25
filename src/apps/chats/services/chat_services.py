import logging
from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.manager import Manager
from django.utils.dateparse import parse_datetime

from apps.chats.models import Conversation
from apps.chats.repositories.inter import IMessageRepo, IConsumerRepo
from apps.chats.exceptions import MessageValidationError, MessageStorageError, MessageRetrievalError, \
    ConversationNotFoundError, TooManyMessageException
from apps.chats.utils import parse_iso_aware

logger = logging.getLogger(__name__)
MyUser = get_user_model()

class ChatService:
    def __init__(self, 
                 user_repo: Manager[MyUser], 
                 conversation_repo: Manager, 
                 redis_repo: IMessageRepo, 
                 db_repo: IMessageRepo,
                 redis_consumer_repo: IConsumerRepo
                 ):
        self.user_repo = user_repo
        self.conversation_repo = conversation_repo
        self.redis_repo = redis_repo
        self.db_repo = db_repo
        self.redis_consumer_repo = redis_consumer_repo

    def create_conversation(self, title: str | None = None) -> str:
        try:
            conv = self.conversation_repo.create(title=title)
            logger.info(f"Conversation created: {conv.id}")
            return str(conv.id)
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise


    def join_conversation(self, conv_id: str, user_id: int):
        try:
            conversation = self.conversation_repo.get(id=conv_id)
            user = self.user_repo.get(id=user_id)
            conversation.participants.add(user)
            self.add_active_user(conv_id, user_id)
            logger.info(f"User {user_id} joined conversation {conv_id}")
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {conv_id} does not exist")
            raise ConversationNotFoundError(conv_id)
        except MyUser.DoesNotExist:
            logger.error(f"User {user_id} does not exist")
            raise ValidationError(f"User {user_id} does not exist")
        except Exception as e:
            logger.error(f"Error joining conversation {conv_id} for user {user_id}: {e}")
            raise

    def leave_conversation(self, conv_id: str, user_id: int):
        try:
            conversation = self.conversation_repo.get(id=conv_id)
            user = self.user_repo.get(id=user_id)
            conversation.participants.remove(user)
            self.remove_active_user(conv_id, user_id)
            logger.info(f"User {user_id} left conversation {conv_id}")
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {conv_id} does not exist")
            raise ConversationNotFoundError(conv_id)
        except MyUser.DoesNotExist:
            logger.error(f"User {user_id} does not exist")
            raise ValidationError(f"User {user_id} does not exist")
        except Exception as e:
            logger.error(f"Error leaving conversation {conv_id} for user {user_id}: {e}")
            raise

    def send_message(self, conv_id: str, sender_id: int, text: str):
        try:
            message = {
                'sender': sender_id,
                'text': text,
                'timestamp': datetime.now(timezone.utc).isoformat()
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

    def conversation_exists(self, conv_id: str) -> bool:
        try:
            self.conversation_repo.get(id=conv_id)
            logger.info(f"Conversation {conv_id} exists")
            return True
        except Conversation.DoesNotExist:
            logger.error(f"Conversation {conv_id} does not exist")
            raise ConversationNotFoundError(conv_id)
        except Exception as e:
            logger.error(f"Error checking conversation {conv_id} existence: {e}")
            raise e

    def get_all_conversations(self) -> list:
        try:
            conversations = self.conversation_repo.all()
            return [{'id': str(conv.id), 'name': f"Chat {conv.get_title()}"} for conv in conversations]
        except Exception as e:
            logger.error(f"Error retrieving all conversations: {e}")
            raise e

    def add_active_user(self, conv_id: str, user_id: int):
        key = f'active_users:{conv_id}'
        try:
            self.redis_consumer_repo.add_to_set(key, str(user_id))
            logger.info(f"Added user {user_id} to active in {conv_id}")
        except Exception as e:
            logger.error(f"Error adding active user: {e}")
            raise e

    def remove_active_user(self, conv_id: str, user_id: int):
        key = f'active_users:{conv_id}'
        try:
            self.redis_consumer_repo.remove_from_set(key, str(user_id))
            logger.info(f"Removed user {user_id} from active in {conv_id}")
        except Exception as e:
            logger.error(f"Error removing active user: {e}")
            raise e

    def get_active_user_ids(self, conv_id: str) -> list[str]:
        key = f'active_users:{conv_id}'
        try:
            return self.redis_consumer_repo.get_set_members(key)
        except Exception as e:
            logger.error(f"Error getting active user IDs: {e}")
            raise e

    def get_active_users(self, conv_id: str) -> list[MyUser]:
        try:
            user_ids = self.get_active_user_ids(conv_id)
            if not user_ids:
                return []
            users = self.user_repo.filter(id__in=[int(uid) for uid in user_ids])
            logger.info(f"Retrieved active users for {conv_id}")
            return list(users)
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise e

    def check_throttling_message(self, per_second: int, per_minute: int, user_id: int,
                                 conv_id: str) -> Exception | None:
        try:
            now = datetime.now(timezone.utc)
            messages = self.redis_repo.get_messages_by_user_id(conv_id, user_id)

            if messages:
                last_message = messages[-1]
                last_message_timestamp = last_message.get("timestamp")

                if last_message_timestamp is not None:
                    last_dt = parse_iso_aware(last_message_timestamp)

                    if (now - last_dt).total_seconds() < per_second:
                        raise TooManyMessageException("Too many messages per second")

                    one_minute_ago = now - timedelta(minutes=1)
                    recent_messages = [m for m in messages if parse_iso_aware(m["timestamp"]) > one_minute_ago]

                    if len(recent_messages) > per_minute:
                        raise TooManyMessageException("Too many messages per minute")

            return None

        except TooManyMessageException as e:
            raise e
        except Exception as e:
            logger.error(e)

    def cleanup_conversation_if_empty(self, conv_id: str):
        try:
            active_users = self.get_active_user_ids(conv_id)
            if not active_users:
                self.redis_repo.clear_messages(conv_id)
                key = f'active_users:{conv_id}'
                self.redis_consumer_repo.delete_set(key)
                logger.info(f"Cleaned up Redis cache for empty conversation {conv_id}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")