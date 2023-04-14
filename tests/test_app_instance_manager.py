from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from projects.models import Project

from ..models import AppInstance, Apps

User = get_user_model()


class AppInstaceManagerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.project = Project.objects.create_project(
            name="test-perm", owner=self.user, description="", repository=""
        )
        app = Apps.objects.create(name="Persistent Volume", slug="volumeK8s")

        app_instance = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_1",
            app=app,
            project=self.project,
        )

        app_instance_2 = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_2",
            app=app,
            project=self.project,
        )

        app_instance_3 = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_3",
            app=app,
            project=self.project,
        )

        app_instance.app_dependencies.set([app_instance_2, app_instance_3])

        app_instance_4 = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_4",
            app=app,
            project=self.project,
        )

        app_instance_5 = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_5",
            app=app,
            project=self.project,
        )

        app_instance_4.app_dependencies.set([app_instance_5])

    @override_settings(STUDIO_ACCESSMODE="ReadWriteOnce")
    def test_get_available_app_dependencies_rw_once(self):
        result = AppInstance.objects.get_available_app_dependencies(
            user=self.user, project=self.project, app_name="Persistent Volume"
        )

        self.assertEqual(len(result), 2)

    @override_settings(STUDIO_ACCESSMODE="ReadWriteMany")
    def test_get_available_app_dependencies_rw_many(self):
        result = AppInstance.objects.get_available_app_dependencies(
            user=self.user, project=self.project, app_name="Persistent Volume"
        )

        self.assertEqual(len(result), 5)

    def test_get_available_app_dependencies_setting_default(self):
        result = AppInstance.objects.get_available_app_dependencies(
            user=self.user, project=self.project, app_name="Persistent Volume"
        )

        self.assertEqual(len(result), 5)
