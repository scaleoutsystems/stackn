from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from projects.models import Environment, Project

from ..generate_form import get_form_environments, get_form_primitives
from ..models import AppInstance, Apps

User = get_user_model()


class GenerateFormTestCase(TestCase):
    def setUp(self) -> None:
        self.app_settings_pvc = {
            "volume": {
                "size": {
                    "type": "select",
                    "title": "Size",
                    "default": "1Gi",
                    "user_can_edit": False,
                    "items": [
                        {"name": "1Gi", "value": "1Gi"},
                        {"name": "2Gi", "value": "2Gi"},
                        {"name": "5Gi", "value": "5Gi"},
                    ],
                },
                "accessModes": {
                    "type": "string",
                    "title": "AccessModes",
                    "default": "ReadWriteMany",
                },
                "storageClass": {
                    "type": "string",
                    "title": "StorageClass",
                    "default": "",
                },
            },
            "permissions": {
                "public": {"value": "false", "option": "false"},
                "private": {"value": "false", "option": "true"},
                "project": {"value": "true", "option": "true"},
            },
            "default_values": {"port": "port", "targetport": "targetport"},
            "environment": {
                "name": "from",
                "type": "match",
                "title": "Image",
                "quantity": "one",
            },
        }
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")

        self.project = Project.objects.create_project(
            name="test-perm-generate_form",
            owner=self.user,
            description="",
            repository="",
        )
        self.app = Apps.objects.create(name="Persistent Volume", slug="volumeK8s")
        return super().setUp()

    # primatives

    @override_settings(DISABLED_APP_INSTANCE_FIELDS=[])
    def test_get_form_primitives_should_return_complete(self):
        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_primitives(app_settings, None)

        result_items = result["volume"]
        result_keys = result_items.keys()
        expected_items = self.app_settings_pvc["volume"].items()

        result_length = len(result_items)
        expected_length = len(expected_items) + 1

        self.assertEqual(result_length, expected_length)

        for key, val in expected_items:
            is_in_keys = key in result_keys

            self.assertTrue(is_in_keys)

            is_string = isinstance(val, str)

            if is_string:
                continue

            result_item = result_items[key]

            for _key, _val in val.items():
                result_val = result_item[_key]
                self.assertEqual(result_val, _val)

    @override_settings(DISABLED_APP_INSTANCE_FIELDS=["accessModes", "storageClass"])
    def test_get_form_primitives_should_remove_two(self):
        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_primitives(app_settings, None)

        result_items = result["volume"]
        result_keys = result_items.keys()

        result_length = len(result_items)
        expected_length = 2

        self.assertEqual(result_length, expected_length)

        has_expected_keys = "meta_title" in result_keys and "size" in result_keys

        self.assertTrue(has_expected_keys)

    @override_settings(
        DISABLED_APP_INSTANCE_FIELDS=[
            "accessModes",
            "storageClass",
            "madeUpValue",
        ]
    )
    def test_get_form_primitives_field_not_in_model(self):
        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_primitives(app_settings, None)

        result_items = result["volume"]
        result_keys = result_items.keys()

        result_length = len(result_items)
        expected_length = 2

        self.assertEqual(result_length, expected_length)

        has_expected_keys = "meta_title" in result_keys and "size" in result_keys

        self.assertTrue(has_expected_keys)

    @override_settings(DISABLED_APP_INSTANCE_FIELDS=[])
    def test_get_form_primitives_should_set_default(self):
        app_settings = deepcopy(self.app_settings_pvc)

        app_instance = AppInstance(
            name="My app",
            access="private",
            app=self.app,
            project=self.project,
            parameters={
                "volume": {
                    "size": "5Gi",
                    "accessModes": "ReadWriteMany",
                    "storageClass": "microk8s-hostpath",
                },
            },
            owner=self.user,
        )
        app_instance.save()

        result = get_form_primitives(app_settings, app_instance)

        result_items = result["volume"]

        result_size = result_items["size"]["default"]
        result_size_user_can_edit = result_items["size"]["user_can_edit"]
        result_access_modes = result_items["accessModes"]["default"]
        result_storage_class = result_items["storageClass"]["default"]

        self.assertEqual(result_size, "5Gi")
        self.assertFalse(result_size_user_can_edit)
        self.assertEqual(result_access_modes, "ReadWriteMany")
        self.assertEqual(result_storage_class, "microk8s-hostpath")

        app_instance.parameters = {}

        app_instance.save()

        app_settings_default = deepcopy(self.app_settings_pvc)

        app_instance = AppInstance.objects.get(name="My app")

        result = get_form_primitives(app_settings_default, app_instance)

        result_items = result["volume"]

        result_size = result_items["size"]["default"]
        result_access_modes = result_items["accessModes"]["default"]
        result_storage_class = result_items["storageClass"]["default"]

        self.assertEqual(result_size, "1Gi")
        self.assertEqual(result_access_modes, "ReadWriteMany")
        self.assertEqual(result_storage_class, "")

    # environments

    def test_get_form_environments_single(self):
        environment = Environment(
            app=self.app,
            project=self.project,
            name="test",
            slug="test",
            repository="test-repo",
            image="test-image",
        )

        environment.save()
        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_environments(app_settings, self.project, self.app, None)

        dep_environment, environments = result

        self.assertEqual(dep_environment, True)

        objs = environments["objs"]

        self.assertEqual(len(objs), 1)

        result_item = objs[0]

        self.assertEqual(result_item.name, "test")
        self.assertEqual(result_item.slug, "test")

    def test_get_form_environments_with_public(self):
        environment = Environment(
            app=self.app,
            project=self.project,
            name="test1",
            slug="test1",
            repository="test1-repo",
            image="test1-image",
        )

        environment.save()

        environment2 = Environment(
            app=self.app,
            name="test2",
            slug="test2",
            repository="test2-repo",
            image="test2-image",
            public=True,
        )

        environment2.save()

        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_environments(app_settings, self.project, self.app, None)

        dep_environment, environments = result

        self.assertEqual(dep_environment, True)

        objs = environments["objs"]

        self.assertEqual(len(objs), 2)

        number_of_public = 0

        for obj in objs:
            self.assertIn(obj.name, ["test1", "test2"])
            self.assertIn(obj.slug, ["test1", "test2"])

            if obj.public:
                number_of_public += 1

        self.assertEqual(number_of_public, 1)

    def test_get_form_environments_with_public_and_other_projects(self):
        project = Project.objects.create_project(
            name="test-perm-generate_form2",
            owner=self.user,
            description="",
            repository="",
        )

        environment = Environment(
            app=self.app,
            project=project,
            name="test1",
            slug="test1",
            repository="test1-repo",
            image="test1-image",
        )

        environment.save()

        environment2 = Environment(
            app=self.app,
            name="test2",
            slug="test2",
            repository="test2-repo",
            image="test2-image",
            public=True,
        )

        environment2.save()

        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_environments(app_settings, self.project, self.app, None)

        dep_environment, environments = result

        self.assertEqual(dep_environment, True)

        objs = environments["objs"]

        self.assertEqual(len(objs), 1)

        result_item = objs[0]

        self.assertEqual(result_item.name, "test2")
        self.assertEqual(result_item.slug, "test2")
        self.assertTrue(result_item.public)
