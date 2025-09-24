from rest_framework import serializers

from apps.users.models import MyUser


class MyUserSerializer(serializers.ModelSerializer):
    avatar = serializers.URLField(source='get_avatar')
    
    class Meta:
        model = MyUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'color',
            'avatar',
        ]