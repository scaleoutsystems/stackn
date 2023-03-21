from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from ..models import Project

User = get_user_model()


class ProjectViewTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("foo", "foo@test.com", "bar")
        _ = Project.objects.create_project(
            name="test-perm", owner=user, description="", repository=""
        )
        user = User.objects.create_user("member", "bar@test.com", "bar")
        self.client.login(username="foo", password="bar")

    def test_grant_access_to_project(self):
        """
        Test granting/adding member to a project
        """
        member = User.objects.get(username="member")
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        response = self.client.post(
            reverse(
                "projects:grant_access",
                kwargs={"user": owner, "project_slug": project.slug},
            ),
            {"selected_users": [member.pk]},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(member.has_perm("can_view_project", project))
        self.assertTrue(project.authorized.exists())

    def test_revoke_access_to_project(self):
        """
        Test revoke access of added member to a project
        """
        member = User.objects.get(username="member")
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        assign_perm("can_view_project", member, project)
        project.authorized.add(member)

        _ = self.client.post(
            reverse(
                "projects:revoke_access",
                kwargs={"user": owner, "project_slug": project.slug},
            ),
            {"selected_users": [member.pk]},
        )

        self.assertFalse(member.has_perm("can_view_project", project))
        self.assertFalse(project.authorized.exists())

    def test_forbidden_project_details(self):
        """
        Test non-project member not allowed to access project overview
        """
        self.client.login(username="member", password="bar")
        member = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "projects:details",
                kwargs={"user": member, "project_slug": project.slug},
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_project_settings(self):
        """
        Test non-project member not allowed to access project settings
        """
        self.client.login(username="member", password="bar")
        member = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "projects:settings",
                kwargs={"user": member, "project_slug": project.slug},
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_project_delete(self):
        """
        Test non-project member not allowed to access project delete
        """
        self.client.login(username="member", password="bar")
        member = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "projects:delete",
                kwargs={"user": member, "project_slug": project.slug},
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_project_setS3storage(self):
        """
        Test non-project member not allowed to access project setS3storage
        """
        self.client.login(username="member", password="bar")
        member = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "projects:set_s3storage",
                kwargs={"user": member, "project_slug": project.slug},
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_project_setmlflow(self):
        """
        Test non-project member not allowed to access project setmlflow
        """
        self.client.login(username="member", password="bar")
        member = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "projects:set_mlflow",
                kwargs={"user": member, "project_slug": project.slug},
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)
