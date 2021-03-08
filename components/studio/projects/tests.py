from django.test import TestCase
from django.contrib.auth.models import User
from .models import Environment, Project
import os
from django.conf import settings
from .helpers import decrypt_key
from .tasks import create_settings_file
import yaml


class ProjectTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("admin")
        Project.objects.create(
            name="test-project",
            slug="test-project",
            owner=user,
            project_key="a2V5",
            project_secret="c2VjcmV0"
        )

    def test_create_settings_file(self):
        project = Project.objects.get(name="test-project")

        proj_settings = dict()
        proj_settings['active'] = 'stackn'
        proj_settings['client_id'] = 'studio-api'
        proj_settings['realm'] = settings.KC_REALM
        proj_settings['active_project'] = project.slug

        self.assertEqual(create_settings_file(project.slug), yaml.dump(proj_settings))

    def test_decrypt_key(self):
        project = Project.objects.filter(name="test-project").first()

        self.assertEqual(decrypt_key(project.project_key), "key")
        self.assertEqual(decrypt_key(project.project_secret), "secret")
