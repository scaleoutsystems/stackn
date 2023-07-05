from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import MLFlow, Project

User = get_user_model()


class CreateMLFlowTestCase(TestCase):
    project_name = "test-perm-mlflow"

    def setUp(self) -> None:
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.project = Project.objects.create_project(
            name=self.project_name,
            owner=self.user,
            description="",
            repository="",
        )

    def test_no_default_for_project(self):
        obj = MLFlow(
            name="mlflow1",
            project=self.project,
            owner=self.user,
        )

        obj.save()

        project = Project.objects.get(name=self.project_name)

        self.assertEqual(project.mlflow.name, obj.name)

    def test_default_existis_for_project(self):
        obj = MLFlow(
            name="mlflow1",
            project=self.project,
            owner=self.user,
        )

        obj.save()

        project = Project.objects.get(name=self.project_name)

        self.assertEqual(project.mlflow.name, obj.name)

        obj2 = MLFlow(
            name="mlflow2",
            project=self.project,
            owner=self.user,
        )

        obj2.save()

        project = Project.objects.get(name=self.project_name)

        self.assertEqual(project.mlflow.name, obj.name)
