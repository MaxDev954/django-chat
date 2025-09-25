from typing import Dict, List
import redis
import json
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.chats.exceptions import MessageStorageError, MessageRetrievalError
from apps.chats.repositories.inter import IMessageRepo, IConsumerRepo, IMessageClearRepo
from apps.chats.validators import validate_message_required_field
from loggers import get_redis_logger

logger = get_redis_logger()
MyUser = get_user_model()


class RedisMessageRepo(IMessageClearRepo):
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def push_message(self, conv_id: str, message: Dict) -> None:
        try:
            if not validate_message_required_field(message):
                raise ValueError("The message must contain sender, text, timestamp")

            self.redis_client.rpush(f"chat:{conv_id}", json.dumps(message))
            logger.info(f"Message saved in conversation {conv_id}")
        except redis.RedisError as e:
            logger.error(f"Error saving message to Redis: {e}")
            raise MessageStorageError(e)


    def get_messages(self, conv_id: str) -> List[Dict]:
        try:
            messages = self.redis_client.lrange(f"chat:{conv_id}", 0, -1)
            return [json.loads(m) for m in messages]
        except redis.RedisError as e:
            logger.error(f"Error receiving messages from Redis: {e}")
            raise MessageRetrievalError(e)
        except json.JSONDecodeError as e:
            logger.error(f"Message deserialization error: {e}")
            raise MessageRetrievalError(e)

    def get_messages_by_user_id(self,conv_id: str, user_id: int) -> list[Dict]:
        try:
            raw_messages = self.redis_client.lrange(f"chat:{conv_id}", 0, -1)
            messages = [json.loads(m) for m in raw_messages]

            if messages:
                return [m for m in messages if int(m.get("sender")) == user_id]

            return []
        except redis.RedisError as e:
            logger.error(f"Error receiving messages from Redis: {e}")
            raise MessageRetrievalError(e)
        except json.JSONDecodeError as e:
            logger.error(f"Message deserialization error: {e}")
            raise MessageRetrievalError(e)

    def clear_messages(self, conv_id: str):
        try:
            key = f"chat:{conv_id}"
            deleted_count = self.redis_client.delete(key)

            if deleted_count:
                logger.info(f"Cleared messages from Redis for conversation {conv_id}")
            else:
                logger.info(f"No messages found in Redis for conversation {conv_id}")

        except redis.RedisError as e:
            logger.error(f"Error clearing messages from Redis for conversation {conv_id}: {e}")
            raise MessageStorageError(f"Failed to clear Redis messages: {e}")
        except Exception as e:
            logger.error(f"Unexpected error clearing messages from Redis: {e}")
            raise MessageStorageError(f"Failed to clear Redis messages: {e}")

class RedisConsumerRepo(IConsumerRepo):
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def add_to_set(self, key: str, value: str):
        try:
            self.redis.sadd(key, value)
        except redis.RedisError as e:
            message = f"Redis error adding to set: {e}"
            logger.error(message)
            raise MessageStorageError(message)

    def remove_from_set(self, key: str, value: str):
        try:
            self.redis.srem(key, value)
        except redis.RedisError as e:
            message = f"Redis error removing from set: {e}"
            logger.error(message)
            raise MessageStorageError(message)

    def get_set_members(self, key: str) -> List[str]:
        try:
            return [m.decode('utf-8') for m in self.redis.smembers(key)]
        except redis.RedisError as e:
            message = f"Redis error getting set members: {e}"
            logger.error(message)
            raise MessageRetrievalError(message)

    def delete_set(self, key: str):
        try:
            set_size = self.redis.scard(key)
            if set_size == 0:
                deleted_count = self.redis.delete(key)
                if deleted_count:
                    logger.info(f"Deleted empty set '{key}'")
            else:
                logger.info(f"Set '{key}' not deleted - contains {set_size} members")
        except redis.RedisError as e:
            message = f"Redis error deleting set '{key}': {e}"
            logger.error(message)
            raise MessageStorageError(message)