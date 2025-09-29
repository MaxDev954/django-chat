import os
from django.core.exceptions import ValidationError


def validate_signup_data(data: dict):
    if not data.get('first_name') or not data.get('last_name'):
        raise ValidationError("First and last names are required")
    if not data.get('email') or '@' not in data['email']:
        raise ValidationError("Invalid email")
    if not data.get('password'):
        raise ValidationError("Password is required")


def validate_image_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.heic']

    if ext not in valid_extensions:
        raise ValidationError('File extension not supported')