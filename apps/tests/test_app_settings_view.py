from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from projects.models import Project

from ..models import AppCategories, AppInstance, Apps

User = get_user_model()


class AppSettingsViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.category = AppCategories.objects.create(
            name="Network", priority=100, slug="network"
        )
        self.app = Apps.objects.create(
            name="Jupyter Lab",
            slug="jupyter-lab",
            user_can_edit=False,
            category=self.category,
            settings={
                "apps": {"Persistent Volume": "many"},
                "flavor": "one",
                "default_values": {"port": "80", "targetport": "8888"},
                "environment": {
                    "name": "from",
                    "title": "Image",
                    "quantity": "one",
                    "type": "match",
                },
                "permissions": {
                    "public": {"value": "false", "option": "false"},
                    "project": {"value": "true", "option": "true"},
                    "private": {"value": "false", "option": "true"},
                },
                "export-cli": "True",
            },
        )

        self.project = Project.objects.create_project(
            name="test-perm",
            owner=self.user,
            description="",
            repository="",
        )

        self.app_instance = AppInstance.objects.create(
            access="public",
            owner=self.user,
            name="test_app_instance_public",
            app=self.app,
            project=self.project,
            parameters={
                "environment": {"pk": ""},
            },
        )

    def get_data(self, user=None):
        project = Project.objects.create_project(
            name="test-perm",
            owner=user if user is not None else self.user,
            description="",
            repository="",
        )

        return project

    def test_user_can_edit_true(self):
        c = Client()

        response = c.post(
            "/accounts/login/", {"username": "foo1", "password": "bar"}
        )
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = (
            f"/{self.user.username}/{self.project.slug}/"
            + f"apps/settings/{self.app_instance.id}"
        )

        response = c.get(url)

        self.assertEqual(response.status_code, 403)

    def test_user_can_edit_false(self):
        c = Client()

        response = c.post(
            "/accounts/login/", {"username": "foo1", "password": "bar"}
        )
        response.status_code

        self.assertEqual(response.status_code, 302)

        self.app.user_can_edit = True
        self.app.save()

        url = (
            f"/{self.user.username}/{self.project.slug}/"
            + f"apps/settings/{self.app_instance.id}"
        )

        response = c.get(url)

        self.assertEqual(response.status_code, 200)
