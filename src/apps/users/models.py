from colorfield.fields import ColorField
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models

from apps.users.utils import generate_random_color
from apps.users.validators import validate_image_extension


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """

        values_error = [
            (email, 'Users must have an email address'),
            (password, 'Users must have a password')
        ]

        for field, msg in values_error:
            if not field: raise ValueError(msg)

        user = self.model(
            email=self.normalize_email(email),
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, **kwargs):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            **kwargs
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser):
    email = models.EmailField(verbose_name='Email', max_length=255, unique=True)
    first_name = models.CharField(verbose_name='First name', max_length=255,null=True, blank=True)
    last_name = models.CharField(verbose_name='Last name', max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    color = ColorField(default=generate_random_color)
    avatar = models.FileField(validators=[validate_image_extension], upload_to='images/avatars/', blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = MyUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        return self.is_admin