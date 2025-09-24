from datetime import datetime
from typing import Literal

from django.contrib.auth import get_user_model
from django.http import SimpleCookie
from apps.users.serializers import MyUserSerializer

MyUser = get_user_model()

def create_user_status_message(user: MyUser, status: Literal['joined' ,'left']) -> dict:
    return {
        'type': 'user_status',
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'user': MyUserSerializer(user).data
    }


def get_cookie_from_scope(scope, name: str):
    cookie_header = dict(scope['headers']).get(b'cookie', b'').decode()
    cookie = SimpleCookie()
    cookie.load(cookie_header)
    if name in cookie:
        return cookie[name].value
    return None