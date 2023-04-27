from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from projects.models import Project

from ..views import UpdatePatternView

User = get_user_model()


class SetDefaultPatternToProjectTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")

    @override_settings(PROJECTS_PER_USER_LIMIT=None)
    def test_is_as_unique_as_possible(self):
        view = UpdatePatternView()

        for _ in range(30):
            project = Project.objects.create_project(
                name="test-perm-SetDefaultPatternToProjectTestCase",
                owner=self.user,
                description="",
                repository="",
            )

            result = view.validate(project.pattern)
            self.assertTrue(result)

        projects = Project.objects.filter(owner=self.user)

        self.assertEqual(projects.count(), 30)

        is_unique = projects.distinct("pattern").count() == projects.count()

        self.assertTrue(is_unique)

        project = Project.objects.create_project(
            name="test-perm",
            owner=self.user,
            description="",
            repository="",
        )

        projects = Project.objects.filter(owner=self.user)

        self.assertEqual(projects.count(), 31)

        is_unique = projects.distinct("pattern").count() == projects.count()

        self.assertFalse(is_unique)
