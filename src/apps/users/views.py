from django.contrib.auth import get_user_model, login, logout
from django.shortcuts import render, redirect
from apps.users.forms import LoginForm, SignupForm
from apps.users.services.auth_services import AuthService
from loggers import get_django_logger

logger = get_django_logger()
MyUser = get_user_model()

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
    auth_service = AuthService(MyUser.objects)
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user_data = auth_service.signup(form.cleaned_data)
                logger.info(f"User signed up: {user_data['email']}")
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