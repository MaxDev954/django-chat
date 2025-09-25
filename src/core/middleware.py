from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        if not request.user.is_authenticated:
            allowed_paths = [reverse('login'), reverse('signup')]
            if request.path not in allowed_paths:
                return redirect(reverse('login'))
        return self.get_response(request)