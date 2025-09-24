from django.urls import re_path
from apps.chats import consumers

websocket_urlpatterns = [
    re_path(r"ws/conversation/", consumers.ConversationConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<conv_id>[a-f0-9\-]+)/$', consumers.ChatConsumer.as_asgi()),
]