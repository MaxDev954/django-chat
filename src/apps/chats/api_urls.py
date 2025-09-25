from django.urls import path, include
from rest_framework import routers

from apps.chats.views import ConversationViewSet

router = routers.DefaultRouter()
router.register('', ConversationViewSet, 'conversation')

urlpatterns = [
    path('', include(router.urls))
]