from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


def run(*args):
    admin = User.objects.get(username="admin")
    try:
        _ = Token.objects.get(user=admin)
    except Token.DoesNotExist:
        _ = Token.objects.create(user=admin)
