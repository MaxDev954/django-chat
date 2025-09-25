import json
from datetime import datetime, timezone, timedelta
from unittest import mock
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.chats.exceptions import TooManyMessageException, MessageStorageError, MessageRetrievalError
from apps.chats.models import Conversation
from apps.chats.repositories import DatabaseMessageRepo
from apps.chats.repositories.inter import IMessageRepo, IConsumerRepo
from apps.chats.services.chat_services import ChatService

MyUser = get_user_model()

class ChatServiceTestCase(TestCase):
    def setUp(self):
        self.user1 = MyUser.objects.create_user(
            first_name='user1', last_name='user1',
            email='test1@example.com', password='pass'
        )
        self.user2 = MyUser.objects.create_user(
            first_name='user2', last_name='user2',
            email='test2@example.com', password='pass'
        )

        self.mock_redis_repo = mock.MagicMock(spec=IMessageRepo)
        self.mock_redis_consumer_repo = mock.MagicMock(spec=IConsumerRepo)

        self.db_repo = DatabaseMessageRepo()

        self.service = ChatService(
            user_repo=MyUser.objects,
            conversation_repo=Conversation.objects,
            redis_repo=self.mock_redis_repo,
            db_repo=self.db_repo,
            redis_consumer_repo=self.mock_redis_consumer_repo
        )

    def test_create_conversation_success(self):
        conv_id = self.service.create_conversation(title="Test Chat")
        conv = Conversation.objects.get(id=conv_id)
        self.assertEqual(conv.title, "Test Chat")

    def test_join_leave_conversation(self):
        conv_id = self.service.create_conversation(title="Chat 1")

        # join
        self.service.join_conversation(conv_id, self.user1.id)
        self.service.join_conversation(conv_id, self.user2.id)

        conv = Conversation.objects.get(id=conv_id)
        self.assertIn(self.user1, conv.participants.all())
        self.assertIn(self.user2, conv.participants.all())
        self.mock_redis_consumer_repo.add_to_set.assert_called_with(
            f'active_users:{conv_id}', str(self.user2.id)
        )

        # leave
        self.service.leave_conversation(conv_id, self.user1.id)
        conv.refresh_from_db()
        self.assertNotIn(self.user1, conv.participants.all())
        self.mock_redis_consumer_repo.remove_from_set.assert_called_with(
            f'active_users:{conv_id}', str(self.user1.id)
        )

    def test_send_message_calls_redis_and_db(self):
        conv_id = self.service.create_conversation(title="Chat 2")
        self.service.join_conversation(conv_id, self.user1.id)

        self.service.send_message(conv_id, self.user1.id, "Hello World")

        self.mock_redis_repo.push_message.assert_called_once()
        messages = self.db_repo.get_messages(conv_id)
        self.assertEqual(messages[0]['text'], "Hello World")

    def test_get_active_users_returns_users(self):
        conv_id = self.service.create_conversation(title="Chat 3")
        self.service.join_conversation(conv_id, self.user1.id)
        self.service.join_conversation(conv_id, self.user2.id)

        self.mock_redis_consumer_repo.get_set_members.return_value = [
            str(self.user1.id), str(self.user2.id)
        ]

        active_users = self.service.get_active_users(conv_id)
        self.assertEqual(set(u.id for u in active_users), {self.user1.id, self.user2.id})
        self.mock_redis_consumer_repo.get_set_members.assert_called_once_with(
            f'active_users:{conv_id}'
        )

    def test_conversation_exists(self):
        conv_id = self.service.create_conversation(title="Chat 4")
        exists = self.service.conversation_exists(conv_id)
        self.assertTrue(exists)

        with self.assertRaises(Exception):
            self.service.conversation_exists('9999')


class ThrottlingTests(TestCase):
    def setUp(self):
        self.chat_service = ChatService(
            user_repo=MagicMock(),
            conversation_repo=MagicMock(),
            redis_repo=MagicMock(),
            db_repo=MagicMock(),
            redis_consumer_repo=MagicMock(),
        )
        self.chat_service.redis_repo = MagicMock()

    def test_no_messages(self):
        self.chat_service.redis_repo.get_messages_by_user_id.return_value = []
        result = self.chat_service.check_throttling_message(1, 5, 1, "conv1")
        self.assertIsNone(result)

    def test_per_second_limit_exceeded(self):
        now = datetime.now(timezone.utc)
        last_message = {"sender": 1, "text": "hi", "timestamp": now.isoformat()}
        self.chat_service.redis_repo.get_messages_by_user_id.return_value = [last_message]

        with self.assertRaises(TooManyMessageException) as cm:
            self.chat_service.check_throttling_message(per_second=10, per_minute=5, user_id=1, conv_id="conv1")
        self.assertIn("Too many messages per second", str(cm.exception))

    def test_per_minute_limit_exceeded(self):
        now = datetime.now(timezone.utc)
        messages = [
            {"sender": 1, "text": f"msg{i}", "timestamp": (now - timedelta(seconds=i*5)).isoformat()}
            for i in range(6)
        ]
        self.chat_service.redis_repo.get_messages_by_user_id.return_value = messages

        with self.assertRaises(TooManyMessageException) as cm:
            self.chat_service.check_throttling_message(per_second=1, per_minute=5, user_id=1, conv_id="conv1")
        self.assertIn("Too many messages per minute", str(cm.exception))

    def test_okay_messages(self):
        now = datetime.now(timezone.utc)
        messages = [
            {"sender": 1, "text": "hi", "timestamp": (now - timedelta(seconds=20)).isoformat()},
            {"sender": 1, "text": "hello", "timestamp": (now - timedelta(seconds=15)).isoformat()},
        ]
        self.chat_service.redis_repo.get_messages_by_user_id.return_value = messages

        result = self.chat_service.check_throttling_message(per_second=1, per_minute=5, user_id=1, conv_id="conv1")
        self.assertIsNone(result)


class TestCleanupConversationIfEmpty(TestCase):

    def setUp(self):
        self.user_repo_mock = MagicMock()
        self.conversation_repo_mock = MagicMock()
        self.redis_repo_mock = MagicMock()
        self.db_repo_mock = MagicMock()
        self.redis_consumer_repo_mock = MagicMock()

        self.chat_service = ChatService(
            user_repo=self.user_repo_mock,
            conversation_repo=self.conversation_repo_mock,
            redis_repo=self.redis_repo_mock,
            db_repo=self.db_repo_mock,
            redis_consumer_repo=self.redis_consumer_repo_mock
        )

        self.conv_id = "test-conversation-123"

    def test_cleanup_conversation_if_empty_success(self):
        self.redis_consumer_repo_mock.get_set_members.return_value = []

        self.chat_service.cleanup_conversation_if_empty(self.conv_id)

        self.redis_consumer_repo_mock.get_set_members.assert_called_once_with(f'active_users:{self.conv_id}')
        self.redis_repo_mock.clear_messages.assert_called_once_with(self.conv_id)
        self.redis_consumer_repo_mock.delete_set.assert_called_once_with(f'active_users:{self.conv_id}')

    def test_cleanup_conversation_with_active_users(self):
        self.redis_consumer_repo_mock.get_set_members.return_value = ['1', '2']

        self.chat_service.cleanup_conversation_if_empty(self.conv_id)

        self.redis_consumer_repo_mock.get_set_members.assert_called_once_with(f'active_users:{self.conv_id}')
        self.redis_repo_mock.clear_messages.assert_not_called()
        self.redis_consumer_repo_mock.delete_set.assert_not_called()

    @patch('apps.chats.services.chat_services.logger')
    def test_cleanup_conversation_redis_error_on_get_active_users(self, mock_logger):
        self.redis_consumer_repo_mock.get_set_members.side_effect = MessageRetrievalError("Redis connection failed")

        self.chat_service.cleanup_conversation_if_empty(self.conv_id)

        self.assertEqual(mock_logger.error.call_count, 2)
        self.redis_repo_mock.clear_messages.assert_not_called()
        self.redis_consumer_repo_mock.delete_set.assert_not_called()

    @patch('apps.chats.services.chat_services.logger')
    def test_cleanup_conversation_redis_error_on_clear_messages(self, mock_logger):
        self.redis_consumer_repo_mock.get_set_members.return_value = []
        self.redis_repo_mock.clear_messages.side_effect = MessageStorageError("Failed to clear messages")

        self.chat_service.cleanup_conversation_if_empty(self.conv_id)

        self.redis_consumer_repo_mock.get_set_members.assert_called_once()
        self.redis_repo_mock.clear_messages.assert_called_once_with(self.conv_id)
        mock_logger.error.assert_called_once()
        self.redis_consumer_repo_mock.delete_set.assert_not_called()

    @patch('apps.chats.services.chat_services.logger')
    def test_cleanup_conversation_redis_error_on_delete_set(self, mock_logger):
        self.redis_consumer_repo_mock.get_set_members.return_value = []
        self.redis_consumer_repo_mock.delete_set.side_effect = MessageStorageError("Failed to delete set")

        self.chat_service.cleanup_conversation_if_empty(self.conv_id)

        self.redis_consumer_repo_mock.get_set_members.assert_called_once()
        self.redis_repo_mock.clear_messages.assert_called_once_with(self.conv_id)
        self.redis_consumer_repo_mock.delete_set.assert_called_once_with(f'active_users:{self.conv_id}')
        mock_logger.error.assert_called_once()


    def test_cleanup_conversation_empty_string_conv_id(self):
        self.redis_consumer_repo_mock.get_set_members.return_value = []
        empty_conv_id = ""

        self.chat_service.cleanup_conversation_if_empty(empty_conv_id)

        self.redis_consumer_repo_mock.get_set_members.assert_called_once_with('active_users:')

    def test_cleanup_conversation_none_conv_id(self):
        self.redis_consumer_repo_mock.get_set_members.return_value = []

        self.chat_service.cleanup_conversation_if_empty(None)

        self.redis_consumer_repo_mock.get_set_members.assert_called_once_with('active_users:None')

