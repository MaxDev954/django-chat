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

class MyUserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_null=False)
    first_name = serializers.CharField(required=True, allow_null=False)
    last_name = serializers.CharField(required=True, allow_null=False)
    password1 = serializers.CharField(required=True, allow_null=False)
    password2 = serializers.CharField(required=True, allow_null=False)

    class Meta:
        model = MyUser
        fields = [
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
        ]

    def validate(self, attrs):
        if attrs["password1"] != attrs["password2"]:
            raise serializers.ValidationError("Passwords don't match")
        return attrs


class MyUserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_null=False)
    password = serializers.EmailField(required=True, allow_null=False)

    class Meta:
        model = MyUser
        fields = [
            'email',
            'password'
        ]