from django.urls import path
from .views import login_form_view, signup_view

urlpatterns = [
    path("login/", login_form_view, name="login"),
    path("signup/", signup_view, name="signup"),
]