from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from apps.users.models import MyUser
from apps.users.validators import validate_signup_data


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "your@email.com"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            user = MyUser.objects.filter(email=email).first()
            if not user or not user.check_password(password):
                raise ValidationError("Invalid email or password.")
        return cleaned_data


class SignupForm(forms.Form):
    first_name = forms.CharField(
        label="First Name",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "John"}),
    )
    last_name = forms.CharField(
        label="Last Name",
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Doe"}),
    )
    email = forms.EmailField(
        label="Email",
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "your@email.com"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
    )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if MyUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            validate_password(password)
        return password


    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise ValidationError("Passwords do not match.")

        validate_signup_data(cleaned_data)
        return cleaned_data