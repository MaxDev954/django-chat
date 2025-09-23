import json
from datetime import datetime
from time import timezone

import redis
from unittest import TestCase
from unittest.mock import patch, MagicMock
from apps.chats.exceptions import MessageStorageError, MessageRetrievalError
from apps.chats.repositories import RedisMessageRepo


class RedisMessageRepoTests(TestCase):
    def setUp(self):
        patcher = patch("apps.chats.repositories.redis_repo.redis.from_url")
        self.addCleanup(patcher.stop)
        self.mock_from_url = patcher.start()
        self.mock_redis_client = MagicMock()
        self.mock_from_url.return_value = self.mock_redis_client
        self.repo = RedisMessageRepo(url="redis://test")

    def test_push_message_success(self):
        message = {"sender": "user1", "text": "Hello", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()}
        self.repo.push_message("conv1", message)
        self.mock_redis_client.rpush.assert_called_once_with("chat:conv1", json.dumps(message))

    def test_push_message_validation_error(self):
        invalid_message = {"sender": "user1", "text": "Hello"}  # немає timestamp
        with self.assertRaises(ValueError):
            self.repo.push_message("conv1", invalid_message)

    def test_push_message_redis_error(self):
        message = {"sender": "user1", "text": "Hello", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()}
        self.mock_redis_client.rpush.side_effect = redis.RedisError("Redis error")
        with self.assertRaises(MessageStorageError):
            self.repo.push_message("conv1", message)

    def test_get_messages_success(self):
        stored_messages = [
            json.dumps({"sender": "user1", "text": "Hi", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()}),
            json.dumps({"sender": "user2", "text": "Hello", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()}),
        ]
        self.mock_redis_client.lrange.return_value = stored_messages
        messages = self.repo.get_messages("conv1")
        self.assertEqual(messages, [
            {"sender": "user1", "text": "Hi", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()},
            {"sender": "user2", "text": "Hello", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()},
        ])

    def test_get_messages_redis_error(self):
        self.mock_redis_client.lrange.side_effect = redis.RedisError("Redis error")
        with self.assertRaises(MessageRetrievalError):
            self.repo.get_messages("conv1")

    def test_get_messages_json_error(self):
        self.mock_redis_client.lrange.return_value = ["not json"]
        with self.assertRaises(MessageRetrievalError):
            self.repo.get_messages("conv1")