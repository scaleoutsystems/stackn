from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Project

User = get_user_model()


class ProjectViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("foo", "foo@test.com", "bar")
        cls.project_name = "test-title"
        cls.project = Project.objects.create_project(name=cls.project_name, owner=cls.user, description="", repository="")

    def setUp(self):
        self.client.login(username="foo", password="bar")

    def get_project_page(self, page: str):
        return self.client.get(
                reverse(
                    f"projects:{page}",
                    kwargs={"user": self.user, "project_slug": self.project.slug}
                    )
                )

    def test_project_overview(self):
        resp = self.get_project_page("details")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "projects/overview.html")
        self.assertContains(resp, f"<title>Project | SciLifeLab Serve</title>")


class FrobiddenProjectViewTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("foo", "foo@test.com", "bar")
        _ = Project.objects.create_project(name="test-perm", owner=user, description="", repository="")
        user = User.objects.create_user("member", "bar@test.com", "bar")
        self.client.login(username="foo", password="bar")

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
