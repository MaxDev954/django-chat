import hashlib
import requests
from django.conf import settings
from django.core.files.base import ContentFile
from loggers import get_django_logger

logger = get_django_logger()

class GravatarService:
    def __init__(self, base_url=None):
        self.base_url = base_url or settings.GRAVATAR_URL

    def get_avatar_url(self, email: str, size: int = 100, default: str = 'identicon', rating: str = 'g') -> str:
        email_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
        return f"{self.base_url}{email_hash}?s={size}&d={default}&r={rating}"

    def save_gravatar_to_user_avatar(self, user: 'CustomUser'):
        try:
            url = self.get_avatar_url(user.email)
            response = requests.get(url)

            if response.status_code == 200:
                img_content = response.content
                filename = f"{user.first_name}_{user.id}_avatar.jpg"
                user.avatar.save(filename, ContentFile(img_content), save=True)
            else:
                logger.error(f"Gravatar returned status {response.status_code} for user {user.first_name}")

        except Exception as e:
            logger.error(
                f"Failed to save Gravatar avatar for user {user.first_name}: {e}",
                exc_info=True
            )
