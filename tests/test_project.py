from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from ..helpers import decrypt_key
from ..models import Project

User = get_user_model()


class ProjectTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("admin", "foo@test.com")
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
        user = User.objects.create_user("member", "bar@test.com")

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

    @override_settings(PROJECTS_PER_USER_LIMIT=1)
    def test_user_can_create(self):
        user = User.objects.get(username="member")
        result = Project.objects.user_can_create(user)

        self.assertTrue(result)

        _ = Project.objects.create(
            name="test-perm1", owner=user, description="", repository=""
        )

        result = Project.objects.user_can_create(user)

        self.assertFalse(result)

    @override_settings(PROJECTS_PER_USER_LIMIT=None)
    def test_user_can_create_should_handle_none(self):
        user = User.objects.get(username="member")
        result = Project.objects.user_can_create(user)

        self.assertTrue(result)

        _ = Project.objects.create(
            name="test-perm1", owner=user, description="", repository=""
        )

        result = Project.objects.user_can_create(user)

        self.assertTrue(result)

    @override_settings(PROJECTS_PER_USER_LIMIT=0)
    def test_user_can_create_should_handle_zero(self):
        user = User.objects.get(username="member")
        result = Project.objects.user_can_create(user)

        self.assertFalse(result)

    @override_settings(PROJECTS_PER_USER_LIMIT=1)
    def test_user_can_create_with_permission(self):
        content_type = ContentType.objects.get_for_model(Project)
        project_permissions = Permission.objects.filter(
            content_type=content_type
        )

        add_permission = next(
            (
                perm
                for perm in project_permissions
                if perm.codename == "add_project"
            ),
            None,
        )

        user = User.objects.get(username="member")

        _ = Project.objects.create(
            name="test-perm1", owner=user, description="", repository=""
        )

        result = Project.objects.user_can_create(user)

        self.assertFalse(result)

        user.user_permissions.add(add_permission)
        user = User.objects.get(username="member")

        result = Project.objects.user_can_create(user)

        self.assertTrue(result)

    @override_settings(PROJECTS_PER_USER_LIMIT=1)
    def test_create_project_raises_exception(self):
        user = User.objects.get(username="member")

        _ = Project.objects.create(
            name="test-perm1", owner=user, description="", repository=""
        )

        with self.assertRaisesMessage(
            Exception, "User not allowed to create project"
        ):
            _ = Project.objects.create_project(
                name="test-perm", owner=user, description="", repository=""
            )

    @override_settings(PROJECTS_PER_USER_LIMIT=0)
    def test_admin_can_create(self):
        superuser = User.objects.create_superuser(
            "superuser", "test@example.com", "123"
        )

        result = Project.objects.user_can_create(superuser)
        self.assertTrue(result)

        user = User.objects.get(username="member")

        result = Project.objects.user_can_create(user)
        self.assertFalse(result)
