from django.contrib.auth import get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from apps.users.forms import LoginForm, SignupForm
from apps.users.serializers import MyUserRegisterSerializer
from apps.users.services.auth_services import AuthService
from loggers import get_django_logger

logger = get_django_logger()
MyUser = get_user_model()
auth_service = AuthService(MyUser.objects)

def login_form_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = MyUser.objects.filter(email=email).first()
            login(request, user)
            logger.info(f"User logged in: {email}")
            return redirect("select_room")
    else:
        form = LoginForm()
    return render(request, "users/login_form.html", {"form": form})

def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = auth_service.signup(form.cleaned_data)
                login(request, user)
                logger.info(f"User signed up: {user.email}")
                return redirect("select_room")
            except Exception as e:
                logger.error(f"Signup error: {e}")
                form.add_error(None, str(e))
    else:
        form = SignupForm()
    return render(request, "users/register_form.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('login')



@api_view(['POST'])
def register_api_view(request: Request):
    serialized_data = MyUserRegisterSerializer(data=request.data)
    serialized_data.is_valid(raise_exception=True)

    try:
        user = auth_service.register(serialized_data.validated_data)
        login(request, user)
        return Response({"detail": "User registered and logged in"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'detail': e.args}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_api_view(request: Request):
    try:
        user = auth_service.login(request.data)
        login(request, user)
        return Response({"detail": "Logged in"}, status=status.HTTP_200_OK)
    except ValidationError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_api_view(request: Request):
    logout(request)
    return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)