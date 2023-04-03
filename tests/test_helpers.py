from django.test import TestCase, override_settings

from apps.helpers.get_apps_per_project_limit import get_apps_per_project_limit


class HelpersTestCase(TestCase):
    @override_settings(
        APPS_PER_PROJECT_LIMIT={
            "vscode": 1,
            "volumeK8s": 2,
            "pytorch-serve": 0,
            "tensorflow-serve": None,
        }
    )
    def test_get_apps_limit_per_user(self):
        result = get_apps_per_project_limit("vscode")
        self.assertEqual(1, result)

        result = get_apps_per_project_limit("volumeK8s")
        self.assertEqual(2, result)

        result = get_apps_per_project_limit("pytorch-serve")
        self.assertEqual(0, result)

        result = get_apps_per_project_limit("tensorflow-serve")
        self.assertIsNone(result)

        result = get_apps_per_project_limit("no-app")
        self.assertIsNone(result)

    @override_settings(APPS_PER_PROJECT_LIMIT={})
    def test_get_apps_limit_per_user_handle_empty(self):
        result = get_apps_per_project_limit("vscode")
        self.assertIsNone(result)

    @override_settings(APPS_PER_PROJECT_LIMIT=None)
    def test_get_apps_limit_per_user_handle_none(self):
        result = get_apps_per_project_limit("vscode")
        self.assertIsNone(result)
