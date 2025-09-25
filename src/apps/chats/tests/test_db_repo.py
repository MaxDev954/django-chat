from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.chats.models import Conversation, Message
from apps.chats.repositories import DatabaseMessageRepo, RedisMessageRepo
from apps.chats.exceptions import MessageStorageError, MessageRetrievalError
from unittest.mock import patch, MagicMock
from datetime import datetime

MyUser = get_user_model()

class DatabaseMessageRepoTests(TestCase):
    def setUp(self):
        self.repo = DatabaseMessageRepo()
        self.user = MyUser.objects.create_user(first_name="user1", last_name='user1', email='example@gmail.com', password="pass")
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user)
        self.repo.client = MagicMock()

    def test_push_message_success(self):
        message = {
            "sender": self.user.id,
            "text": "Hello",
            "timestamp": datetime.now()
        }
        self.repo.push_message(str(self.conversation.id), message)
        saved_message = Message.objects.get(conversation=self.conversation, sender=self.user)
        self.assertEqual(saved_message.text, "Hello")

    def test_push_message_validation_error(self):
        message = {
            "sender": self.user.id,
            "text": "Hello"
        }
        with self.assertRaises(MessageStorageError):
            self.repo.push_message(str(self.conversation.id), message)

    def test_push_message_nonexistent_user_or_conversation(self):
        message = {
            "sender": 9999,
            "text": "Hello",
            "timestamp": datetime.now()
        }
        with self.assertRaises(MessageStorageError):
            self.repo.push_message(str(self.conversation.id), message)

    def test_get_messages_success(self):
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            text="Hi",
            timestamp=datetime(2025, 1, 1, 12, 0)
        )
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            text="Hello",
            timestamp=datetime(2025, 1, 1, 12, 5)
        )

        messages = self.repo.get_messages(str(self.conversation.id))
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['text'], "Hi")
        self.assertEqual(messages[1]['text'], "Hello")

    @patch("apps.chats.repositories.db_repo.Message.objects.filter")
    def test_get_messages_exception(self, mock_filter):
        mock_filter.side_effect = Exception("DB error")
        with self.assertRaises(MessageRetrievalError):
            self.repo.get_messages(str(self.conversation.id))

