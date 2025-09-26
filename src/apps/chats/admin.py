from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "get_title", "created_at")
    search_fields = ("title", "id")
    filter_horizontal = ("participants",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "text", "timestamp")
    list_filter = ("conversation",)
    search_fields = ("text", "sender__username", "conversation__title")
    date_hierarchy = "timestamp"
