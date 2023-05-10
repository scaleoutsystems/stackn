from copy import deepcopy

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from projects.models import Project

from ..generate_form import get_form_primitives
from ..models import AppInstance, Apps

User = get_user_model()


class GenerateFormTestCase(TestCase):
    def setUp(self) -> None:
        self.app_settings_pvc = {
            "volume": {
                "size": {"type": "string", "title": "Size", "default": "1Gi"},
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
        }
        self.user = User.objects.create_user("foo1", "foo@test.com", "bar")

        self.project = Project.objects.create_project(
            name="test-perm-generate_form",
            owner=self.user,
            description="",
            repository="",
        )
        self.app = Apps.objects.create(
            name="Persistent Volume", slug="volumeK8s"
        )
        return super().setUp()

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

    @override_settings(
        DISABLED_APP_INSTANCE_FIELDS=["accessModes", "storageClass"]
    )
    def test_get_form_primitives_should_remove_two(self):
        app_settings = deepcopy(self.app_settings_pvc)

        result = get_form_primitives(app_settings, None)

        result_items = result["volume"]
        result_keys = result_items.keys()

        result_length = len(result_items)
        expected_length = 2

        self.assertEqual(result_length, expected_length)

        has_expected_keys = (
            "meta_title" in result_keys and "size" in result_keys
        )

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

        has_expected_keys = (
            "meta_title" in result_keys and "size" in result_keys
        )

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
        result_access_modes = result_items["accessModes"]["default"]
        result_storage_class = result_items["storageClass"]["default"]

        self.assertEqual(result_size, "5Gi")
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
