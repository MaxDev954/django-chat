import json
from unittest import mock

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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

