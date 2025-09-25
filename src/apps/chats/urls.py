from django.urls import path, include
from rest_framework import routers
from apps.chats.views import ConversationViewSet, room_select_create_view, chat_dashboard_view, room_not_found_view

router = routers.DefaultRouter()
router.register('', ConversationViewSet, 'conversation')

urlpatterns = [
    path('room_not_found/', room_not_found_view, name='chat_not_found'),
    path('select_room/', room_select_create_view, name='select_room'),
    path('room/<str:chat_id>/', chat_dashboard_view, name='chat'),
]