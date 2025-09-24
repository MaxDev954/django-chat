from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.users.models import MyUser
from apps.users.services.gravatar_service import GravatarService
from loggers import get_django_logger

logger = get_django_logger()

@receiver(post_save, sender=MyUser)
def create_user_avatar(sender, instance, created, **kwargs):
    if created and not instance.avatar:
        try:
            GravatarService().save_gravatar_to_user_avatar(instance)
            logger.info(f"Avatar successfully generated for user {instance.username}")
        except Exception as e:
            logger.error(
                f"Failed to generate avatar for user {instance.username}: {e}",
                exc_info=True
            )