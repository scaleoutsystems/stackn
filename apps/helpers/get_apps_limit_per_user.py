from django.conf import settings


def get_apps_limit_per_user(slug):
    """get_apps_limit_per_user

    Args:
        slug (App.slug): slug for the app type

    Returns:
        Integer or None: returns the limit or None if not set
    """
    try:
        apps_per_user_limit = settings.APPS_PER_USER_LIMIT if settings.APPS_PER_USER_LIMIT is not None else {}
    except Exception:
        apps_per_user_limit = {}

    return apps_per_user_limit[slug] if slug in apps_per_user_limit else None
