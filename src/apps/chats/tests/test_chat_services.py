import uuid
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.chats.models import Conversation, Message
from apps.chats.exceptions import MessageValidationError, MessageStorageError, MessageRetrievalError
from datetime import datetime

from apps.chats.repositories import RedisMessageRepo, DatabaseMessageRepo
from apps.chats.services.chat_services import ChatService

MyUser = get_user_model()


class ChatServiceTests(TestCase):
    def setUp(self):
        self.user1 = MyUser.objects.create(first_name='user1', last_name='user1', email='user1@example.com')
        self.user2 = MyUser.objects.create(first_name='user2', last_name='user2', email='user2@example.com')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

        self.user_repo = MagicMock()
        self.conversation_repo = MagicMock()
        self.redis_repo = MagicMock(spec=RedisMessageRepo)
        self.db_repo = MagicMock(spec=DatabaseMessageRepo)

        self.chat_service = ChatService(
            user_repo=self.user_repo,
            conversation_repo=self.conversation_repo,
            redis_repo=self.redis_repo,
            db_repo=self.db_repo
        )

    def test_create_conversation_success(self):
        self.user_repo.objects.filter.return_value = [self.user1, self.user2]
        self.conversation_repo.objects.create.return_value = self.conversation

        conv_id = self.chat_service.create_conversation([self.user1.id, self.user2.id])

        self.user_repo.objects.filter.assert_called_with(id__in=[self.user1.id, self.user2.id])
        self.conversation_repo.objects.create.assert_called_once()
        self.assertEqual(conv_id, str(self.conversation.id))

    def test_create_conversation_no_valid_participants(self):
        self.user_repo.objects.filter.return_value = []

        with self.assertRaises(ValidationError):
            self.chat_service.create_conversation([self.user1.id, self.user2.id])

    def test_create_conversation_exception(self):
        self.user_repo.objects.filter.side_effect = Exception("Database error")

        with self.assertRaises(Exception):
            self.chat_service.create_conversation([self.user1.id, self.user2.id])

    def test_send_message_success(self):
        message = {
            'sender': self.user1.id,
            'text': 'Hello',
            'timestamp': datetime.now().isoformat()
        }

        self.chat_service.send_message(str(self.conversation.id), self.user1.id, 'Hello')

        self.redis_repo.push_message.assert_called_with(str(self.conversation.id), message)
        self.db_repo.push_message.assert_called_with(str(self.conversation.id), message)

    def test_send_message_validation_error(self):
        self.redis_repo.push_message.side_effect = MessageValidationError("Invalid message")

        with self.assertRaises(MessageValidationError):
            self.chat_service.send_message(str(self.conversation.id), self.user1.id, '')

    def test_send_message_storage_error(self):
        self.redis_repo.push_message.side_effect = MessageStorageError("Storage error")

        with self.assertRaises(MessageStorageError):
            self.chat_service.send_message(str(self.conversation.id), self.user1.id, 'Hello')

    def test_send_message_unexpected_error(self):
        self.redis_repo.push_message.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            self.chat_service.send_message(str(self.conversation.id), self.user1.id, 'Hello')

    def test_get_messages_from_redis_success(self):
        messages = [
            {'sender': self.user1.id, 'text': 'Hello', 'timestamp': datetime.now().isoformat()}
        ]
        self.redis_repo.get_messages.return_value = messages

        result = self.chat_service.get_messages_from_redis(str(self.conversation.id))

        self.redis_repo.get_messages.assert_called_with(str(self.conversation.id))
        self.assertEqual(result, messages)

    def test_get_messages_from_redis_retrieval_error(self):
        self.redis_repo.get_messages.side_effect = MessageRetrievalError("Redis error")

        with self.assertRaises(MessageRetrievalError):
            self.chat_service.get_messages_from_redis(str(self.conversation.id))

    def test_get_messages_from_redis_unexpected_error(self):
        self.redis_repo.get_messages.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            self.chat_service.get_messages_from_redis(str(self.conversation.id))

    def test_get_messages_from_db_success(self):
        messages = [
            {'sender': self.user1.id, 'text': 'Hello', 'timestamp': datetime.now().isoformat()}
        ]
        self.db_repo.get_messages.return_value = messages

        result = self.chat_service.get_messages_from_db(str(self.conversation.id))

        self.db_repo.get_messages.assert_called_with(str(self.conversation.id))
        self.redis_repo.push_message.assert_called_with(str(self.conversation.id), messages[0])
        self.assertEqual(result, messages)

    def test_get_messages_from_db_retrieval_error(self):
        self.db_repo.get_messages.side_effect = MessageRetrievalError("DB error")

        with self.assertRaises(MessageRetrievalError):
            self.chat_service.get_messages_from_db(str(self.conversation.id))

    def test_get_messages_from_db_unexpected_error(self):
        self.db_repo.get_messages.side_effect = Exception("Unexpected error")

        with self.assertRaises(Exception):
            self.chat_service.get_messages_from_db(str(self.conversation.id))