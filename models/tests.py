import os

import boto3
import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from moto.server import ThreadedMotoServer

from projects.models import S3, Project

from . import views
from .models import Model, ObjectType

User = get_user_model()

os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


class ModelViewTests(TestCase):
    bucket_name = "test-bucket"

    def setUp(self):
        # Set up mocked S3
        self.server = ThreadedMotoServer(port=5000)
        self.server.start()

        s3 = boto3.resource("s3", endpoint_url="http://localhost:5000")
        bucket = s3.Bucket(self.bucket_name)
        bucket.create()
        s3.meta.client.put_object(Bucket=self.bucket_name, Key="public_uid", Body=b"test")
        s3.meta.client.put_object(Bucket=self.bucket_name, Key="test_uid", Body=b"test")
        # Create user
        self.user = User.objects.create_user("foo", "foo@test.com", "bar")

        self.project = Project.objects.create_project(name="test-perm", owner=self.user, description="", repository="")

        new_model = Model(
            uid="test_uid",
            name="test",
            bucket=self.bucket_name,
            description="model_description",
            model_card="",
            project=self.project,
            access="PR",
            s3=S3.objects.create(
                access_key=os.environ.get("AWS_ACCESS_KEY_ID"),
                host="localhost:5000",
                secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                owner=self.user,
                project=self.project,
            ),
        )
        new_model.save()
        self.private_model = new_model
        public_model = Model(
            uid="public_uid",
            name="public",
            bucket=self.bucket_name,
            description="model_description",
            model_card="",
            project=self.project,
            access="PR",
            s3=S3.objects.create(
                access_key=os.environ.get("AWS_ACCESS_KEY_ID"),
                host="localhost:5000",
                secret_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                owner=self.user,
                project=self.project,
            ),
        )
        public_model.save()
        self.client.login(username="foo", password="bar")
        self.client.post(
            reverse(
                "models:publish_model",
                kwargs={
                    "user": self.user,
                    "project": self.project.slug,
                    "id": public_model.id,
                },
            )
        )
        self.client.post(
            reverse(
                "models:publish_model",
                kwargs={
                    "user": self.user,
                    "project": self.project.slug,
                    "id": new_model.id,
                },
            )
        )
        self.client.post(
            reverse(
                "models:unpublish_model",
                kwargs={
                    "user": self.user,
                    "project": self.project.slug,
                    "id": new_model.id,
                },
            )
        )

    def tearDown(self):
        self.server.stop()

    def test_models_view(self):
        # Get correct request
        request = RequestFactory().get(reverse("models:index"))
        response = views.index(request, user=self.user, project=self.project)

        # Check status code
        assert response.status_code == 200
        assert "<title>Models | SciLifeLab Serve</title>" in response.content.decode()

    @pytest.mark.skip(reason="It's not working")
    def test_public_model_details_view(self):
        response = self.client.get(reverse("models:details_public", kwargs={"id": 1}))

        # Check status code
        assert response.status_code == 200
        self.assertTemplateUsed(response, "models/models_details_public.html")
        assert "Model Details" in response.content.decode()
        assert "<title>Model public Details | SciLifeLab Serve</title>" in response.content.decode()

    @pytest.mark.skip(reason="Could not make this work")
    def test_private_model_details_view(self):
        response = self.client.get(
            reverse(
                "models:details_private",
                kwargs={"user": self.user, "project": self.project.name, "id": self.private_model.id},
            )
        )

        # Check status code
        assert response.status_code == 200
        self.assertTemplateUsed(response, "models/models_details_private.html")
        assert "Model Details" in response.content.decode()
        assert "<title>Private model test Details | SciLifeLab Serve</title>" in response.content.decode()

    @pytest.mark.skip(reason="I am even not sure that it's being invoked")
    def test_model_create_view(self):
        response = self.client.get(reverse("models:create", kwargs={"user": self.user, "project": self.project.name}))

        # Check status code
        assert response.status_code == 200
        self.assertTemplateUsed(response, "models/models_details_private.html")
        assert "Model Details" in response.content.decode()
        assert "<title>Private model test Details | SciLifeLab Serve</title>" in response.content.decode()

    @pytest.mark.skip(reason="I think that the project is not created for this")
    def test_models_list_view(self):
        response = self.client.get(reverse("models:list", kwargs={"user": self.user, "project": self.project.name}))
        # Check status code
        assert response.status_code == 200
        self.assertTemplateUsed(response, "models/models_list.html")
        assert "Models" in response.content.decode()
        assert f"<title>{self.project.name} - Models | SciLifeLab Serve</title>" in response.content.decode()


class ModelViewForbidden(TestCase):
    def setUp(self):
        user = User.objects.create_user("foo", "foo@test.com", "bar")

        project = Project.objects.create_project(name="test-perm", owner=user, description="", repository="")

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

        user = User.objects.create_user("member", "bar@test.com", "bar")
        self.client.login(username="member", password="bar")

    def test_forbidden_models_list(self):
        """
        Test non-project member not allowed to access /models
        """
        owner = User.objects.get(username="foo")
        project = Project.objects.get(name="test-perm")
        response = self.client.get(reverse("models:list", kwargs={"user": owner, "project": project.slug}))
        self.assertTemplateUsed(response, "403.html")
        self.assertEqual(response.status_code, 403)
        assert "<title>Page forbidden | SciLifeLab Serve</title>" in response.content.decode()

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
