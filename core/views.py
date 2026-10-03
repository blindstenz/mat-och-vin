from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_control


def home(request):
    if request.user.is_authenticated:
        return redirect("recipes:list")
    return redirect("login")


def signup(request):
    if not settings.ALLOW_SIGNUP:
        raise Http404
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("recipes:list")
    return render(request, "registration/signup.html", {"form": form})


@cache_control(max_age=3600)
def manifest(request):
    data = {
        "name": "Mat & Vin",
        "short_name": "Mat & Vin",
        "description": "Receptbok med vinförslag",
        "lang": "sv",
        "start_url": reverse("recipes:list"),
        "scope": "/",
        "display": "standalone",
        "background_color": "#fbf7f2",
        "theme_color": "#7b2d3a",
        "icons": [
            {"src": static("icons/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("icons/icon-512.png"), "sizes": "512x512", "type": "image/png"},
            {
                "src": static("icons/icon-512-maskable.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json", json_dumps_params={"ensure_ascii": False})


@cache_control(no_cache=True)
def service_worker(request):
    # Served from the site root so the worker controls every page.
    context = {
        "precache": [
            reverse("offline"),
            static("vendor/pico.red.min.css"),
            static("vendor/htmx.min.js"),
            static("css/app.css"),
            static("js/app.js"),
            static("icons/icon-192.png"),
        ],
    }
    return render(request, "core/sw.js", context, content_type="application/javascript")


def offline(request):
    return render(request, "core/offline.html")
