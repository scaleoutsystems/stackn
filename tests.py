from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm

from .helpers import decrypt_key
from .models import Project

User = get_user_model()


class ProjectTestCase(TestCase):
    def setUp(self):

        user = User.objects.create_user("admin")
        Project.objects.create(
            name="test-secret",
            slug="test-secret",
            owner=user,
            project_key="a2V5",
            project_secret="c2VjcmV0",
        )
        _ = Project.objects.create_project(
            name="test-perm", owner=user, description="", repository=""
        )
        user = User.objects.create_user("member")

    def test_decrypt_key(self):
        project = Project.objects.filter(name="test-secret").first()

        self.assertEqual(decrypt_key(project.project_key), "key")
        self.assertEqual(decrypt_key(project.project_secret), "secret")

    def test_owner_can_view_permission(self):
        """
        Ensure that project owner has 'can_view_project' permission
        """
        project = Project.objects.get(name="test-perm")
        self.assertTrue(project.owner.has_perm("can_view_project", project))

    def test_member_can_view_permission(self):
        """
        Ensure that non-project member don't have 'can_view_project' permission
        """
        user = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        self.assertFalse(user.has_perm("can_view_project", project))


class ProjectViewTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("foo", "foo@test.com", "bar")
        _ = Project.objects.create_project(
            name="test-perm", owner=user, description="", repository=""
        )
        user = User.objects.create_user("member", "foo@test.com", "bar")
        self.client.login(username="foo", password="bar")

    def test_create_project_post(self):
        """
        TODO: Make sure this returns the correct redirect
        """
        # self.client.login(username='foo', password='bar')
        response = self.client.post("projects:create")
        self.assertEqual(response.status_code, 302)

    def test_create_project_get(self):
        """
        TODO: Make sure this render the /create page
        for default project template
        """
        response = self.client.get("/create", follow=True)
        self.assertEqual(response.status_code, 200)

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

    def test_transfer_project_owner(self):
        owner = User.objects.get(username="foo")
        new_owner = User.objects.get(username="member")
        project = Project.objects.get(name="test-perm")
        _ = self.client.post(
            reverse(
                "projects:transfer_owner",
                kwargs={"user": owner, "project_slug": project.slug},
            ),
            {"transfer_to": [new_owner.pk]},
        )
        project = Project.objects.get(name="test-perm")
        self.assertEqual(project.owner, new_owner)
        self.assertTrue(new_owner.has_perm("can_view_project", project))
        self.assertTrue(owner in project.authorized.all())
