import json
import uuid
from datetime import datetime, timedelta, timezone

import redis
from unittest import TestCase
from unittest.mock import patch, MagicMock
from apps.chats.exceptions import MessageStorageError, MessageRetrievalError, TooManyMessageException
from apps.chats.repositories import RedisMessageRepo
from apps.chats.repositories.redis_repo import RedisConsumerRepo
from apps.chats.services.chat_services import ChatService


class RedisMessageRepoTests(TestCase):
    def setUp(self):
        patcher = patch("apps.chats.repositories.redis_repo.redis.from_url")
        self.addCleanup(patcher.stop)
        self.mock_from_url = patcher.start()
        self.mock_redis_client = MagicMock()
        self.mock_from_url.return_value = self.mock_redis_client
        self.repo = RedisMessageRepo(redis_client=self.mock_redis_client)

    def test_push_message_success(self):
        message = {"sender": "user1", "text": "Hello", "timestamp": datetime(2025, 1, 1, 12, 0).timestamp()}
        self.repo.push_message("conv1", message)
        self.mock_redis_client.rpush.assert_called_once_with("chat:conv1", json.dumps(message))

    def test_push_message_validation_error(self):
        invalid_message = {"sender": "user1", "text": "Hello"}
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


class RedisMessageUserByIdRepoTests(TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.repo = RedisMessageRepo(redis_client=self.mock_client)

    def test_get_messages_by_user_id_success(self):
        messages = [
            json.dumps({"sender": "1", "text": "hi", "timestamp": "2025-09-25T12:00:00Z"}),
            json.dumps({"sender": "2", "text": "hello", "timestamp": "2025-09-25T12:01:00Z"}),
        ]
        self.repo.redis_client.lrange.return_value = messages
        result = self.repo.get_messages_by_user_id(str(uuid.uuid4()), 1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "hi")

    def test_get_messages_by_user_id_redis_error(self):
        self.repo.redis_client.lrange.side_effect = redis.RedisError("fail")
        with self.assertRaises(MessageRetrievalError):
            self.repo.get_messages_by_user_id(str(uuid.uuid4()), 1)

    def test_get_messages_by_user_id_json_error(self):
        self.repo.redis_client.lrange.return_value = ["not json"]
        with self.assertRaises(MessageRetrievalError):
            self.repo.get_messages_by_user_id(str(uuid.uuid4()), 1)


class TestDeleteSetMethod(TestCase):

    def setUp(self):
        self.redis_client_mock = MagicMock()
        self.redis_consumer_repo = RedisConsumerRepo(self.redis_client_mock)

    @patch('apps.chats.repositories.redis_repo.logger')
    def test_delete_set_empty_set_success(self, mock_logger):
        key = "active_users:test-123"
        self.redis_client_mock.scard.return_value = 0
        self.redis_client_mock.delete.return_value = 1

        self.redis_consumer_repo.delete_set(key)

        self.redis_client_mock.scard.assert_called_once_with(key)
        self.redis_client_mock.delete.assert_called_once_with(key)
        mock_logger.info.assert_called_with(f"Deleted empty set '{key}'")


    @patch('apps.chats.repositories.redis_repo.logger')
    def test_delete_set_non_empty_set(self, mock_logger):
        key = "active_users:test-123"
        self.redis_client_mock.scard.return_value = 3

        self.redis_consumer_repo.delete_set(key)

        self.redis_client_mock.scard.assert_called_once_with(key)
        self.redis_client_mock.delete.assert_not_called()
        mock_logger.info.assert_called_with(f"Set '{key}' not deleted - contains 3 members")

    @patch('apps.chats.repositories.redis_repo.logger')
    def test_delete_set_redis_error_on_scard(self, mock_logger):
        key = "active_users:test-123"
        self.redis_client_mock.scard.side_effect = redis.RedisError("Connection timeout")

        with self.assertRaises(MessageStorageError):
            self.redis_consumer_repo.delete_set(key)

        mock_logger.error.assert_called_once()
        self.redis_client_mock.delete.assert_not_called()

    @patch('apps.chats.repositories.redis_repo.logger')
    def test_delete_set_redis_error_on_delete(self, mock_logger):
        key = "active_users:test-123"
        self.redis_client_mock.scard.return_value = 0
        self.redis_client_mock.delete.side_effect = redis.RedisError("Delete failed")

        with self.assertRaises(MessageStorageError):
            self.redis_consumer_repo.delete_set(key)

        self.redis_client_mock.scard.assert_called_once_with(key)
        self.redis_client_mock.delete.assert_called_once_with(key)
        mock_logger.error.assert_called_once()


class TestCleanupConversationIntegration(TestCase):

    def setUp(self):
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
            self.redis_client.ping()
        except redis.ConnectionError:
            self.skipTest("Redis server not available")

        self.redis_client.flushdb()

        self.redis_consumer_repo = RedisConsumerRepo(self.redis_client)
        self.redis_repo = RedisMessageRepo(self.redis_client)

        self.user_repo_mock = MagicMock()
        self.conversation_repo_mock = MagicMock()
        self.db_repo_mock = MagicMock()

        self.chat_service = ChatService(
            user_repo=self.user_repo_mock,
            conversation_repo=self.conversation_repo_mock,
            redis_repo=self.redis_repo,
            db_repo=self.db_repo_mock,
            redis_consumer_repo=self.redis_consumer_repo
        )

        self.conv_id = "integration-test-123"

    def tearDown(self):
        if hasattr(self, 'redis_client'):
            self.redis_client.flushdb()
            self.redis_client.close()

    def test_cleanup_conversation_real_redis(self):
        self.redis_client.sadd(f'active_users:{self.conv_id}', '1', '2')
        self.redis_client.rpush(f'chat:{self.conv_id}', '{"sender": 1, "text": "test"}')

        self.assertEqual(self.redis_client.scard(f'active_users:{self.conv_id}'), 2)
        self.assertEqual(self.redis_client.llen(f'chat:{self.conv_id}'), 1)

        self.redis_client.srem(f'active_users:{self.conv_id}', '1', '2')
        self.chat_service.cleanup_conversation_if_empty(self.conv_id)

        self.assertEqual(self.redis_client.scard(f'active_users:{self.conv_id}'), 0)
        self.assertEqual(self.redis_client.llen(f'chat:{self.conv_id}'), 0)
        self.assertEqual(self.redis_client.exists(f'active_users:{self.conv_id}'), 0)