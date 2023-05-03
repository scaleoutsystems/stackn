from django.contrib.auth import get_user_model
from django.db.models import Q
from django.test import TestCase, override_settings

from projects.models import Project

from ..models import AppInstance, Apps

User = get_user_model()


class AppInstaceManagerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")
        self.project = Project.objects.create_project(
            name="test-perm-app-instance-manager",
            owner=self.user,
            description="",
            repository="",
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

    # ---------- get_app_instances_of_project ---------- #

    def test_get_app_instances_of_project(self):
        project = Project.objects.create_project(
            name="test-perm-app-instance_manager-2",
            owner=self.user,
            description="",
            repository="",
        )

        app = Apps.objects.create(name="Combiner", slug="combiner")

        app_instance = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_internal",
            app=app,
            project=project,
        )

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project
        )

        self.assertEqual(len(result), 5)

        app_instance.project = self.project
        app_instance.save()

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project
        )

        self.assertEqual(len(result), 6)

        app_instance.access = "private"
        app_instance.save()

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project
        )

        self.assertEqual(len(result), 6)

    def test_get_app_instances_of_project_limit(self):
        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project, limit=3
        )

        self.assertEqual(len(result), 3)

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project
        )

        self.assertEqual(len(result), 5)

    def test_get_app_instances_of_project_filter(self):
        app = Apps.objects.create(name="Combiner", slug="combiner")

        _ = AppInstance.objects.create(
            access="project",
            owner=self.user,
            name="test_app_instance_internal",
            app=app,
            project=self.project,
        )

        def filter_func(slug):
            return Q(app__slug=slug)

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project, filter_func=filter_func("volumeK8s")
        )

        self.assertEqual(len(result), 5)

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project
        )

        self.assertEqual(len(result), 6)

        result = AppInstance.objects.get_app_instances_of_project(
            self.user,
            self.project,
            filter_func=filter_func("non-existing-slug"),
        )

        self.assertEqual(len(result), 0)

    def test_get_app_instances_of_project_order_by(self):
        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project, order_by="name"
        )

        self.assertEqual(len(result), 5)
        self.assertEqual(result.first().name, "test_app_instance_1")
        self.assertEqual(result.last().name, "test_app_instance_5")

        result = AppInstance.objects.get_app_instances_of_project(
            self.user, self.project, order_by="-name"
        )

        self.assertEqual(len(result), 5)
        self.assertEqual(result.first().name, "test_app_instance_5")
        self.assertEqual(result.last().name, "test_app_instance_1")
