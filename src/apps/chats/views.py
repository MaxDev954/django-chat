from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.chats.models import Conversation
from apps.chats.services.notifier import ConversationNotifier
from loggers import get_django_logger

logger = get_django_logger()

class ConversationViewSet(viewsets.ViewSet):
    queryset = Conversation.objects.all()


    def create(self, request, *args, **kwargs):
        title = request.data.get("title")

        if not title:
            return Response(
                {"detail": "title is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            conv = Conversation.objects.create(title=title)
        except Exception as e:
            logger.error(e)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ConversationNotifier.broadcast_conversations_add(str(conv.id))

        return Response(status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None, *args, **kwargs):
        try:
            conv = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist as e:
            logger.error(e)
            return Response(
                status=status.HTTP_404_NOT_FOUND,
            )

        conv_id = str(conv.id)

        try:
            conv.delete()
        except Exception as e:
            logger.error(e)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ConversationNotifier.broadcast_conversations_remove(str(conv_id))

        return Response(status=status.HTTP_204_NO_CONTENT)
