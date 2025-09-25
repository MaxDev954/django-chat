from django.contrib.auth import get_user_model
from django.db.models import Model

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
            raise