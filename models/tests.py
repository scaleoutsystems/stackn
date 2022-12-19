from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from projects.models import Project

from .models import Model, ObjectType

User = get_user_model()


class ModelViewForbidden(TestCase):
    def setUp(self):
        user = User.objects.create_user("foo", "foo@test.com", "bar")

        project = Project.objects.create_project(
            name="test-perm", owner=user, description="", repository=""
        )

        new_model = Model(
            uid="test_uid",
            name="test",
            bucket="",
            description="model_description",
            model_card="",
            project=project,
            access="PR",
        )
        new_model.save()

        user = User.objects.create_user("member", "foo@test.com", "bar")
        self.client.login(username="member", password="bar")

    def test_forbidden_models_list(self):
        """
        Test non-project member not allowed to access /models
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "models:list", kwargs={"user": owner, "project": project.slug}
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_create(self):
        """
        Test non-project member not allowed to access /models/create
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(
            reverse(
                "models:create",
                kwargs={"user": owner, "project": project.slug},
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_details_private(self):
        """
        Test non-project member not allowed to access /models/<int:id>
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:details_private",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_delete(self):
        """
        Test non-project member not allowed to access /models/<int:id>/delete
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:delete",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_publish(self):
        """
        Test non-project member not allowed to access /models/<int:id>/publish
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:publish_model",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_add_tag(self):
        """
        Test non-project member not allowed to access /models/<int:id>/add_tag
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:add_tag_private",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_remove_tag(self):
        """
        Test non-project member not allowed to
        access /models/<int:id>/remove_tag
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:remove_tag_private",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_unpublidh(self):
        """
        Test non-project member not allowed to
        access /models/<int:id>/unpublish
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:unpublish_model",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_access(self):
        """
        Test non-project member not allowed to access /models/<int:id>/access
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:change_access",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_upload(self):
        """
        Test non-project member not allowed to access /models/<int:id>/upload
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:upload_model_headline",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)

    def test_forbidden_models_docker(self):
        """
        Test non-project member not allowed to access /models/<int:id>/docker
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        model = Model.objects.get(name="test")
        response = self.client.get(
            reverse(
                "models:add_docker_image",
                kwargs={
                    "user": owner,
                    "project": project.slug,
                    "id": model.id,
                },
            )
        )
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)


class TestFixtures(TestCase):
    fixtures = ["models/fixtures/objecttype_fixtures.json"]

    def test_objecttype_mlflow(self):
        obj_type = ObjectType.objects.get(slug="mlflow")
        self.assertEqual(obj_type.slug, "mlflow")

    def test_objecttype_tfmodel(self):
        obj_type = ObjectType.objects.get(slug="tensorflow")
        self.assertEqual(obj_type.slug, "tensorflow")

    def test_objecttype_pythonmodel(self):
        obj_type = ObjectType.objects.get(slug="python")
        self.assertEqual(obj_type.slug, "python")

    def test_objecttype_defaultmodel(self):
        obj_type = ObjectType.objects.get(slug="default")
        self.assertEqual(obj_type.slug, "default")

    def test_objecttype_pytorchmodel(self):
        obj_type = ObjectType.objects.get(slug="pytorch")
        self.assertEqual(obj_type.slug, "pytorch")
