from django.contrib.auth import get_user_model
from django.test import TestCase

from projects.models import Project

from ..models import AppInstance, Apps

User = get_user_model()


class AppInstaceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")

    def get_data(self, access):
        project = Project.objects.create_project(name="test-perm", owner=self.user, description="", repository="")
        app = Apps.objects.create(name="FEDn Combiner", slug="combiner")

        app_instance = AppInstance.objects.create(
            access=access,
            owner=self.user,
            name="test_app_instance_private",
            app=app,
            project=project,
        )

        return [project, app, app_instance]

    def test_permission_created_if_private(self):
        project, app, app_instance = self.get_data("private")

        result = self.user.has_perm("can_access_app", app_instance)

        self.assertTrue(result)

    def test_permission_do_note_created_if_project(self):
        project, app, app_instance = self.get_data("project")

        result = self.user.has_perm("can_access_app", app_instance)

        self.assertFalse(result)

    def test_permission_create_if_changed_to_private(self):
        project, app, app_instance = self.get_data("project")

        result = self.user.has_perm("can_access_app", app_instance)

        self.assertFalse(result)

        app_instance.access = "private"
        app_instance.save()

        result = self.user.has_perm("can_access_app", app_instance)

        self.assertTrue(result)

    def test_permission_remove_if_changed_from_project(self):
        project, app, app_instance = self.get_data("private")

        result = self.user.has_perm("can_access_app", app_instance)

        self.assertTrue(result)

        app_instance.access = "project"
        app_instance.save()

        result = self.user.has_perm("can_access_app", app_instance)

        self.assertFalse(result)
