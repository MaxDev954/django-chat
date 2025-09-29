from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import viewsets, status
from rest_framework.response import Response

from apps.chats.forms import ChatRoomForm
from apps.chats.models import Conversation
from apps.chats.serializers import ConversationSerializer
from apps.chats.services.notifier import ConversationNotifier
from apps.chats.utils import get_ws_chat_url, get_ws_conversation_url, get_chat_select_url
from loggers import get_django_logger

logger = get_django_logger()

class ConversationViewSet(viewsets.ViewSet):
    queryset = Conversation.objects.all()

    def list(self, request, *args, **kwargs):
        serialized_data = ConversationSerializer(Conversation.objects.all(), many=True).data
        return Response(serialized_data)

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

        print('sadfsadf')

        return Response({'id':str(conv.id)},status=status.HTTP_201_CREATED)

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

@login_required(login_url='login')
def room_select_create_view(request):
    if request.method == "POST":
        form = ChatRoomForm(request.POST)
        if form.is_valid():
            try:
                title = form.cleaned_data.get('room')
                conv = Conversation.objects.create(title=title)
                logger.info(f"Room create: {conv.id}")
                return redirect('chat', conv.id)
            except Exception as e:
                logger.error(f'Room Creation failed: {e}')
                form.add_error(None, str(e))

    else:
        form = ChatRoomForm()

    return render(request, 'chat/create_select_room.html', {'form': form, 'ws_conversation_url': get_ws_conversation_url()})

@login_required(login_url='login')
def chat_dashboard_view(request, chat_id):
    try:
        conv = Conversation.objects.get(id=chat_id)
    except Exception as e:
        logger.error(f'chat dashboard failed: {e}')
        return redirect('chat_not_found')

    return render(request, 'chat/chat_dashboard.html',{
        'chat_id': conv.id,
        'chat_name':conv.get_title(),
        'ws_chat_url': get_ws_chat_url(conv.id),
        'chat_select_url': get_chat_select_url(),
        'user_id': request.user.id
    })

def room_not_found_view(request):
    return render(request, 'chat/not_found.html')