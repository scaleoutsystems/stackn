from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings

from projects.models import Project

from ..models import AppInstance, Apps

User = get_user_model()


class CreateAppViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.app = Apps.objects.create(
            name="Jupyter Lab",
            slug="jupyter-lab",
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

    def get_data(self, user=None):
        project = Project.objects.create_project(
            name="test-perm",
            owner=user if user is not None else self.user,
            description="",
            repository="",
        )

        return project

    @override_settings(
        APPS_PER_PROJECT_LIMIT={
            "jupyter-lab": 1,
        }
    )
    def test_has_permission(self):
        c = Client()

        project = self.get_data()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 200)

    @override_settings(APPS_PER_PROJECT_LIMIT={"jupyter-lab": 0})
    def test_has_reached_app_limit(self):
        c = Client()

        project = self.get_data()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 403)

        response = c.post(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 403)

    @override_settings(APPS_PER_PROJECT_LIMIT={"jupyter-lab": 1})
    def test_missing_access_to_project(self):
        c = Client()

        user = User.objects.create_user("foo12", "foo2@test.com", "bar2")

        project = self.get_data(user)

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 403)

        response = c.post(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 403)

    @override_settings(
        APPS_PER_PROJECT_LIMIT={
            "jupyter-lab": None,
        }
    )
    def test_has_permission_when_none(self):
        c = Client()

        project = self.get_data()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 200)

    @override_settings(APPS_PER_PROJECT_LIMIT={})
    def test_has_permission_when_not_specified(self):
        c = Client()

        project = self.get_data()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 200)

    @override_settings(
        APPS_PER_PROJECT_LIMIT={
            "jupyter-lab": 1,
        }
    )
    def test_has_permission_project_level(self):
        c = Client()

        project = self.get_data()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 200)

        project = self.get_data()

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 200)

        _ = AppInstance.objects.create(
            access="private",
            owner=self.user,
            name="test_app_instance_private",
            app=self.app,
            project=project,
        )

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 403)

    @override_settings(APPS_PER_PROJECT_LIMIT={"jupyter-lab": 0})
    def test_permission_overrides_reached_app_limit(self):
        c = Client()

        project = self.get_data()

        response = c.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 403)

        content_type = ContentType.objects.get_for_model(AppInstance)
        project_permissions = Permission.objects.filter(content_type=content_type)

        add_permission = next(
            (perm for perm in project_permissions if perm.codename == "add_appinstance"),
            None,
        )

        self.user.user_permissions.add(add_permission)

        self.user = User.objects.get(username="foo1")

        response = c.get(f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab")

        self.assertEqual(response.status_code, 200)

    @override_settings(APPS_PER_PROJECT_LIMIT={"jupyter-lab": 1})
    def test_app_limit_is_per_project(self):
        c = Client()

        project = self.get_data()

        response = c.post(
            "/accounts/login/", {"username": "foo1", "password": "bar"}
        )
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(
            f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 200)

        user2 = User.objects.create_user("foo123", "foo123@test.com", "bar123")

        project.authorized.add(user2)
        project.save()

        response = c.get(
            f"/{user2.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 200)

        _ = AppInstance.objects.create(
            access="private",
            owner=self.user,
            name="test_app_instance_private",
            app=self.app,
            project=project,
        )

        response = c.get(
            f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 403)

        response = c.get(
            f"/{user2.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(APPS_PER_PROJECT_LIMIT={"jupyter-lab": 1})
    def test_app_limit_altered_for_project(self):
        c = Client()

        project = self.get_data()

        response = c.post(
            "/accounts/login/", {"username": "foo1", "password": "bar"}
        )
        response.status_code

        self.assertEqual(response.status_code, 302)

        project.apps_per_project["jupyter-lab"] = 0

        project.save()

        response = c.get(
            f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(APPS_PER_PROJECT_LIMIT={"jupyter-lab": 1})
    def test_app_limit_altered_for_project_v2(self):
        c = Client()

        project = self.get_data()

        response = c.post(
            "/accounts/login/", {"username": "foo1", "password": "bar"}
        )
        response.status_code

        self.assertEqual(response.status_code, 302)

        response = c.get(
            f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 200)

        _ = AppInstance.objects.create(
            access="private",
            owner=self.user,
            name="test_app_instance_private",
            app=self.app,
            project=project,
        )

        response = c.get(
            f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 403)

        project.apps_per_project["jupyter-lab"] = 2

        project.save()

        response = c.get(
            f"/{self.user.username}/{project.slug}/apps/create/jupyter-lab"
        )

        self.assertEqual(response.status_code, 200)
