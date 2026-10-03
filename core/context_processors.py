from django.conf import settings


def site(request):
    return {"ALLOW_SIGNUP": settings.ALLOW_SIGNUP}
