from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session

from apps.chats.utils import get_cookie_from_scope


class AuthRequiredMiddleware(BaseMiddleware):
    @database_sync_to_async
    def get_user_from_session(self, session_key):
        try:
            session = Session.objects.get(session_key=session_key)
            user_id = session.get_decoded().get('_auth_user_id')
            if user_id:
                from django.contrib.auth import get_user_model
                MyUser = get_user_model()
                return MyUser.objects.get(id=user_id)
        except Session.DoesNotExist:
            return AnonymousUser()
        return AnonymousUser()

    async def __call__(self, scope, receive, send):
        print(scope)
        session_key = get_cookie_from_scope(scope, 'sessionid')
        if session_key:
            user = await self.get_user_from_session(session_key)
            scope["user"] = user
        else:
            scope["user"] = AnonymousUser()

        if not scope["user"].is_authenticated:
            await send({
                "type": "websocket.close",
                "code": 4001,
            })
            return

        return await super().__call__(scope, receive, send)