from unittest import mock
from unittest.mock import patch, MagicMock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from apps.users.models import MyUser
from apps.users.services.auth_services import AuthService
from apps.users.services.gravatar_service import GravatarService


class MyUserModelTest(TestCase):

    def test_create_user(self):
        user = MyUser.objects.create_user(
            email="test@example.com",
            password="password123",
            first_name="John",
            last_name="Doe"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.check_password("password123"))
        self.assertFalse(getattr(user, 'is_admin', False))

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            MyUser.objects.create_user(
                email=None,
                password="password123",
                first_name="John",
                last_name="Doe"
            )

    def test_create_superuser(self):
        superuser = MyUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            first_name="Admin",
            last_name="User"
        )
        self.assertEqual(superuser.email, "admin@example.com")
        self.assertTrue(superuser.is_admin)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.check_password("adminpass"))

    def test_user_str_method(self):
        user = MyUser.objects.create_user(
            email="string@example.com",
            password="password123",
            first_name="Str",
            last_name="Test"
        )
        self.assertEqual(str(user), "string@example.com")

    def test_has_perm_and_has_module_perms(self):
        user = MyUser.objects.create_user(
            email="perm@example.com",
            password="password123",
            first_name="Perm",
            last_name="Test"
        )
        self.assertTrue(user.has_perm("any_perm"))
        self.assertTrue(user.has_module_perms("any_app"))

    def test_is_staff_property(self):
        user = MyUser.objects.create_user(
            email="staff@example.com",
            password="password123",
            first_name="Staff",
            last_name="Test"
        )
        self.assertFalse(user.is_staff)

        superuser = MyUser.objects.create_superuser(
            email="super@example.com",
            password="superpass",
            first_name="Super",
            last_name="User"
        )
        self.assertTrue(superuser.is_staff)


class AuthServiceTest(TestCase):
    def setUp(self):
        self.mock_repo = MagicMock()
        self.service = AuthService(repo=self.mock_repo)

    @patch('apps.users.services.auth_services.validate_signup_data')
    def test_signup_success(self, mock_validator):
        mock_validator.return_value = None
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        self.mock_repo.create_user.return_value = mock_user

        data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword"
        }

        result = self.service.signup(data)

        mock_validator.assert_called_once_with(data)
        self.mock_repo.create_user.assert_called_once_with(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="securepassword"
        )
        self.assertEqual(result.id, 1)

    @patch('apps.users.services.auth_services.validate_signup_data')
    def test_signup_validation_error(self, mock_validator):
        mock_validator.side_effect = ValidationError("Invalid data")
        data = {
            "email": "bademail",
            "first_name": "",
            "last_name": "",
            "password": "pwd"
        }

        with self.assertRaises(ValidationError) as context:
            self.service.signup(data)
        self.assertEqual(str(context.exception), "['Invalid data']")
        self.mock_repo.create_user.assert_not_called()

    @patch('apps.users.services.auth_services.validate_signup_data')
    def test_signup_repo_exception(self, mock_validator):
        mock_validator.return_value = None
        self.mock_repo.create_user.side_effect = Exception("DB error")
        data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "securepassword"
        }

        with self.assertRaises(Exception) as context:
            self.service.signup(data)
        self.assertEqual(str(context.exception), "DB error")
        self.mock_repo.create_user.assert_called_once()

class MyUserAvatarTestCase(TestCase):

    def test_avatar_field_accepts_valid_file(self):
        user = MyUser.objects.create(
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

        image_file = SimpleUploadedFile(
            "avatar.png", b"file_content", content_type="image/png"
        )
        user.avatar = image_file
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_avatar_field_rejects_invalid_file_extension(self):
        user = MyUser(
            email="test2@example.com",
            first_name="Test",
            last_name="User"
        )
        invalid_file = SimpleUploadedFile(
            "avatar.txt", b"file_content", content_type="text/plain"
        )

        user.avatar = invalid_file
        with self.assertRaises(Exception):
            user.full_clean()

    @mock.patch.object(GravatarService, "save_gravatar_to_user_avatar")
    def test_gravatar_service_called_on_user_creation(self, mock_save):
        user = MyUser.objects.create(
            email="gravatar@example.com",
            first_name="Gravatar",
            last_name="Test"
        )

        mock_save.assert_called_once_with(user)