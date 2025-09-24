import redis
from django.conf import settings
from django.contrib.auth import get_user_model

from apps.chats.models import Conversation
from apps.chats.repositories import RedisMessageRepo, DatabaseMessageRepo
from apps.chats.repositories.redis_repo import RedisConsumerRepo
from apps.chats.services.chat_services import ChatService

MyUser = get_user_model()

redis_client = redis.from_url(
            settings.REDIS_URL,
        )

redis_repo = RedisMessageRepo(redis_client)
redis_consumer_repo = RedisConsumerRepo(redis_client)
db_repo = DatabaseMessageRepo()
chat_service = ChatService(
    user_repo=MyUser.objects,
    conversation_repo=Conversation.objects,
    redis_repo=redis_repo,
    db_repo=db_repo,
    redis_consumer_repo=redis_consumer_repo
)
