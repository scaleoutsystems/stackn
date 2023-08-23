from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from guardian.shortcuts import assign_perm

from projects.models import Project

User = get_user_model()


class RevokeAccessToProjectViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.user2 = User.objects.create_user("foo2", "foo2@test.com", "bar")
        self.user3 = User.objects.create_user("foo3", "foo3@test.com", "bar")
        self.client = Client()

    def get_data(self, user=None):
        project = Project.objects.create_project(
            name="test-perm",
            owner=user if user is not None else self.user,
            description="",
            repository="",
        )

        project.authorized.add(self.user2)

        assign_perm("can_view_project", self.user2, project)

        return project

    def test_revoke_access_to_user(self):
        response = self.client.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/revoke",
            {"selected_user": "foo2"},
        )

        self.assertEqual(response.status_code, 302)

        project = Project.objects.get(name="test-perm")

        authorized = project.authorized.all()

        self.assertEquals(len(authorized), 0)

        self.user2 = User.objects.get(username="foo2")

        has_perm = self.user2.has_perm("can_view_project", project)

        self.assertFalse(has_perm)

    def test_revoke_access_non_existing_user(self):
        response = self.client.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/revoke",
            {"selected_user": "non_existing_user"},
        )

        self.assertEqual(response.status_code, 400)

    def test_revoke_access_user_no_access_to_project(self):
        response = self.client.post("/accounts/login/", {"username": "foo1", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        response = self.client.post(
            f"/{self.user.username}/{project.slug}/project/access/revoke",
            {"selected_user": "foo3"},
        )

        self.assertEqual(response.status_code, 400)

    def test_revoke_access_can_not_remove_if_not_owner(self):
        response = self.client.post("/accounts/login/", {"username": "foo2", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        project = self.get_data()

        project.authorized.add(self.user3)

        response = self.client.post(
            f"/{self.user2.username}/{project.slug}/project/access/revoke",
            {"selected_user": "foo3"},
        )

        self.assertEqual(response.status_code, 400)
