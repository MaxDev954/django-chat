from django.test import TestCase
from apps.users.models import MyUser


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
