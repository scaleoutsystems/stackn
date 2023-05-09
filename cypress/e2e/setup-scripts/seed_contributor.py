"""DB seed script for e2e cypress contributor tests."""

import os.path
import json
from django.conf import settings
from django.contrib.auth.models import User
from projects.models import Project


cypress_path = os.path.join(settings.BASE_DIR, "cypress/fixtures")
#print(cypress_path) # /app/cypress/fixtures

with open( os.path.join(cypress_path, "user-contributor.json"), 'r') as f:
    testdata = json.load(f)

    username = testdata["username"]
    email = testdata["email"]
    pwd = testdata["password"]

    # Create the contributor user
    user = User.objects.create_user(username, email, pwd)
    user.save()

    # Create a dummy project to be deleted by the contributor user
    Project.objects.create_project(
        name="e2e-delete-proj-test", owner=user, description="", repository=""
    )
