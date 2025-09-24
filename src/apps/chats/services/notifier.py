from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

class ConversationNotifier:
    @classmethod
    def broadcast_conversations_add(cls, _id: str):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "conversations",
            {"type": "add_conversation", "id": _id}
        )

    @classmethod
    def broadcast_conversations_remove(cls, _id: str):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "conversations",
            {"type": "remove_conversation", "id": _id}
        )