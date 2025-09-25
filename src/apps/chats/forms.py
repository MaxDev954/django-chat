from django import forms
from django.core.exceptions import ValidationError


class ChatRoomForm(forms.Form):
    room = forms.CharField(
        label="Room name",
        max_length=10,
        widget=forms.TextInput(attrs={"placeholder": "Room 1"}),
    )

