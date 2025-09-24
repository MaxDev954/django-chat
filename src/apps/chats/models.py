import uuid
from django.contrib.auth import get_user_model
from django.db import models

MyUser = get_user_model()

class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=10, blank=True, null=True)
    participants = models.ManyToManyField(MyUser)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_title(self):
        return self.title or str(self.id)[:10]

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField()
