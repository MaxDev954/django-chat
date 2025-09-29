from django.contrib.auth import get_user_model, authenticate
from rest_framework.exceptions import ValidationError

from apps.users.models import MyUserManager
from apps.users.validators import validate_signup_data
from loggers import get_django_logger

logger = get_django_logger()
MyUser = get_user_model()

class AuthService:
    def __init__(self, repo: MyUserManager):
        self.repo = repo

    def signup(self, data: dict) -> MyUser:
        validate_signup_data(data)

        try:
            user = self.repo.create_user(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data.get('password'),
            )
            logger.info(f"User created: {user.email}")
            return user
        except Exception as e:
            logger.error(f"Signup error: {e}")
            raise e

    def login(self, data: dict) -> MyUser:
        email = data.get("email")
        password = data.get("password")

        user = authenticate(email=email, password=password)

        if not user:
            logger.error(f"Login failed for {email}")
            raise ValidationError("Incorrect email or password")

        logger.info(f"User logged in: {user.email}")
        return user

    def register(self, data):
        try:
            user = self.repo.create_user(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password1']
            )
            return user
        except Exception as e:
            logger.error(f'Register error: {e}')
            raise e

