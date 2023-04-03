from django.conf import settings


def get_apps_per_project_limit(slug):
    """get_apps_per_project_limit

    Args:
        slug (App.slug): slug for the app type

    Returns:
        Integer or None: returns the limit or None if not set
    """
    try:
        apps_per_project_limit = (
            settings.APPS_PER_PROJECT_LIMIT
            if settings.APPS_PER_PROJECT_LIMIT is not None
            else {}
        )
    except Exception:
        apps_per_project_limit = {}

    return (
        apps_per_project_limit[slug]
        if slug in apps_per_project_limit
        else None
    )
