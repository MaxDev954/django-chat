from datetime import datetime, timezone
from typing import Literal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import SimpleCookie
from django.urls import reverse

from apps.users.serializers import MyUserSerializer

MyUser = get_user_model()

def create_user_status_message(user: MyUser, status: Literal['joined' ,'left']) -> dict:
    return {
        'type': 'user_status',
        'status': status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'user': MyUserSerializer(user).data
    }

def create_conversation_status_message(_id: str, status: Literal['joined' ,'left']) -> dict:
    return {
        'type': 'conversation_status',
        'status': status,
        'id': _id
    }

def get_cookie_from_scope(scope, name: str):
    cookie_header = dict(scope['headers']).get(b'cookie', b'').decode()
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    if name in cookie:
        return cookie[name].value
    return None

def parse_iso_aware(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def get_ws_chat_url(conversation_id: str):
    return f'ws://{settings.DOMAIN}/ws/chat/{conversation_id}/'

def get_ws_conversation_url():
    return f'ws://{settings.DOMAIN}/ws/conversation/'

def get_chat_select_url():
    url = reverse('select_room')
    url = url[1:]
    return f'{settings.HOST}{url}'