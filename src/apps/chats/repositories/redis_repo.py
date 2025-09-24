from typing import Dict, List
import redis
import json
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.chats.exceptions import MessageStorageError, MessageRetrievalError
from apps.chats.repositories.inter import IMessageRepo, IConsumerRepo
from apps.chats.validators import validate_message_required_field
from loggers import get_redis_logger

logger = get_redis_logger()
MyUser = get_user_model()


class RedisMessageRepo(IMessageRepo):
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