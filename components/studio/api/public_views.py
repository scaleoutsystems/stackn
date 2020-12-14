from django.conf import settings
from django.http import JsonResponse


def get_studio_settings(request):
    """
    This view should return a list of settings
    needed to set up the CLI client.
    """
    studio_settings = []

    studio_url = {
        "name": "studio_host",
        "value": settings.STUDIO_HOST
    }
    kc_url = {
        "name": "keycloak_host",
        "value": settings.KC_URL
    }

    studio_settings.append(studio_url)
    studio_settings.append(kc_url)

    return JsonResponse({'data': studio_settings})
