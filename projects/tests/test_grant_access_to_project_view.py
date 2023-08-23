from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from projects.models import Project

User = get_user_model()


class GrantAccessToProjectViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.user2 = User.objects.create_user("foo2", "foo2@test.com", "bar")
        self.user3 = User.objects.create_user("client1", "foo3@test.com", "bar")
        self.client = Client()

    def get_data(self, user=None):
        project = Project.objects.create_project(
            name="test-perm",
            owner=user if user is not None else self.user,
            description="",
            repository="",
        )

        return project

    def test_grant_access_to_user(self):
        response = self.client.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/grant",
            {"selected_user": "foo2"},
        )

        self.assertEqual(response.status_code, 302)

        project = Project.objects.get(name="test-perm")

        authorized = project.authorized.all()

        self.assertEquals(len(authorized), 1)

        authorized_user = authorized[0]

        self.assertEqual(authorized_user.id, self.user2.id)

        self.user2 = User.objects.get(username="foo2")

        has_perm = self.user2.has_perm("can_view_project", project)

        self.assertTrue(has_perm)

    def test_grant_access_to_user_no_access(self):
        response = self.client.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data(user=self.user2)

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/grant",
            {"selected_user": "foo2"},
        )

        self.assertEqual(response.status_code, 403)

    def test_grant_access_to_non_existing_user(self):
        response = self.client.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/grant",
            {"selected_user": "non_existing_user"},
        )

        self.assertEqual(response.status_code, 302)

        project = Project.objects.get(name="test-perm")

        authorized = project.authorized.all()

        self.assertEquals(len(authorized), 0)

    """
    THIS TEST FAILS ON SCALEOUT DUE TO is_client does not exist
    def test_grant_access_to_client(self):
        response = self.client.post(
            "/accounts/login/", {"username": "foo1", "password": "bar"}
        )
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/grant",
            {"selected_user": "client1"},
        )

        self.assertEqual(response.status_code, 302)

        project = Project.objects.get(name="test-perm")

        authorized = project.authorized.all()

        self.assertEquals(len(authorized), 0)
    """
