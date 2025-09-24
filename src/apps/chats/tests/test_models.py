import uuid
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.chats.models import Conversation, Message

MyUser = get_user_model()


class ConversationModelTests(TestCase):
    def setUp(self):
        self.user1 = MyUser.objects.create_user(email="test@gmail.com1", first_name="user1", last_name="user1", password="pass")
        self.user2 = MyUser.objects.create_user(email="test@gmail.com2", first_name="user2", last_name="user2", password="pass")

    def test_create_conversation_with_participants(self):
        conv = Conversation.objects.create(title="Chat1")
        conv.participants.add(self.user1, self.user2)

        self.assertEqual(conv.title, "Chat1")
        self.assertIn(self.user1, conv.participants.all())
        self.assertIn(self.user2, conv.participants.all())
        self.assertIsNotNone(conv.created_at)

    def test_get_title_returns_title_if_exists(self):
        conv = Conversation.objects.create(title="Hello")
        self.assertEqual(conv.get_title(), "Hello")

    def test_get_title_returns_id_prefix_if_no_title(self):
        conv = Conversation.objects.create(title=None)
        expected_prefix = str(conv.id)[:10]
        self.assertEqual(conv.get_title(), expected_prefix)


class MessageModelTests(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create_user(first_name="user1", last_name='user1', email='test@example.com', password="pass")
        self.conv = Conversation.objects.create(title="Test Chat")
        self.conv.participants.add(self.user)

    def test_create_message(self):
        msg = Message.objects.create(
            conversation=self.conv,
            sender=self.user,
            text="Hello!",
            timestamp=timezone.now(),
        )

        self.assertEqual(msg.text, "Hello!")
        self.assertEqual(msg.conversation, self.conv)
        self.assertEqual(msg.sender, self.user)

    def test_message_ordering(self):
        ts1 = timezone.now()
        ts2 = ts1 + timezone.timedelta(seconds=5)

        msg1 = Message.objects.create(
            conversation=self.conv, sender=self.user, text="First", timestamp=ts1
        )
        msg2 = Message.objects.create(
            conversation=self.conv, sender=self.user, text="Second", timestamp=ts2
        )

        messages = list(self.conv.messages.order_by("timestamp"))
        self.assertEqual(messages, [msg1, msg2])
