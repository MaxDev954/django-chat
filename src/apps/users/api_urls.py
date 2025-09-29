from django.urls import path

from apps.users.views import login_api_view, logout_api_view, register_api_view

urlpatterns = [
    path("login/", login_api_view),
    path("register/", register_api_view),
    path("logout/", logout_api_view),
]