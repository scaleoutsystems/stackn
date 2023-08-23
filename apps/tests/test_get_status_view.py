from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from projects.models import Project

from ..models import AppCategories, AppInstance, Apps

User = get_user_model()


class GetStatusViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.category = AppCategories.objects.create(name="Network", priority=100, slug="network")
        self.app = Apps.objects.create(
            name="Jupyter Lab",
            slug="jupyter-lab",
            user_can_edit=False,
            category=self.category,
        )

        self.project = Project.objects.create_project(
            name="test-perm-get_status",
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

    def test_user_has_access(self):
        c = Client()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = f"/{self.user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": [self.app_instance.id]})

        self.assertEqual(response.status_code, 200)

    def test_user_has_no_access(self):
        c = Client()

        url = f"/{self.user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": [self.app_instance.id]})

        self.assertEqual(response.status_code, 403)

        user = User.objects.create_user("foo2", "foo2@test.com", "bar")

        response = c.post("/accounts/login/", {"username": "foo2", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = f"/{user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": [self.app_instance.id]})

        self.assertEqual(response.status_code, 403)

    def test_apps_empty(self):
        c = Client()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = f"/{self.user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": []})

        self.assertEqual(response.status_code, 200)
