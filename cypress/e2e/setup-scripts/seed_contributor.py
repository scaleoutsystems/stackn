"""DB seed script for e2e cypress contributor tests."""

from django.contrib.auth.models import User
from projects.models import Project


USERNAME = "e2e_tests_contributor_tester"
EMAIL = "no-reply-contributor@scilifelab.se"
PWD = "test12345"


# Create the contributor user
user = User.objects.create_user(USERNAME, EMAIL, PWD)
user.save()

# Create a dummy project to be deleted by the contributor user
Project.objects.create_project(
    name="e2e-delete-proj-test", owner=user, description="", repository=""
)
