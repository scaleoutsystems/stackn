from django import template

from apps.models import AppInstance

register = template.Library()


# settings value
@register.simple_tag
def can_create_app(user, project, app):
    app_slug = app if isinstance(app, str) else app.slug

    user_can_create = AppInstance.objects.user_can_create(user=user, project=project, app_slug=app_slug)

    return user_can_create
