from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


def run(*args):
    admin = User.objects.get(username="admin")
    _ = Token.objects.create(user=admin)
