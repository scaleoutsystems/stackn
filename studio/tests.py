from django.contrib.auth import get_user_model
from django.test import TestCase
from guardian.shortcuts import assign_perm, remove_perm

from apps.models import AppInstance, Apps
from projects.models import Project
from scripts.app_instance_permissions import run

User = get_user_model()


class AppInstancePermissionScriptTestCase(TestCase):
    def get_data(self, user, access):
        project = Project.objects.create_project(
            name="test-perm", owner=user, description="", repository=""
        )
        app = Apps.objects.create(name="FEDn Combiner")

        app_instance = AppInstance.objects.create(
            access=access,
            owner=user,
            name="test_app_instance_private",
            app=app,
            project=project,
        )

        return [project, app, app_instance]

    def test_permissions_are_added(self):
        user = User.objects.create_user("foo1", "foo@test.com", "bar")

        project, app, app_instance = self.get_data(user, "private")

        remove_perm("can_access_app", user, app_instance)

        run()

        has_perm = user.has_perm("can_access_app", app_instance)

        self.assertTrue(has_perm)

    def test_permissions_are_removed(self):
        user = User.objects.create_user("foo1", "foo@test.com", "bar")

        project, app, app_instance = self.get_data(user, "project")

        assign_perm("can_access_app", user, app_instance)

        run()

        has_perm = user.has_perm("can_access_app", app_instance)

        self.assertFalse(has_perm)
