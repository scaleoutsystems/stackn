from django.test import TestCase
from django.contrib.auth.models import User
from .models import Environment, Project
import os
from django.conf import settings
from .helpers import create_settings_file
import yaml


class ProjectTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user("admin")
        environment = Environment.objects.create(
            name="test-project-env",
            image="test-project-env"
        )
        Project.objects.create(
            name="test-project",
            slug="test-project",
            owner=user,
            project_key="key",
            project_secret="secret",
            environment=environment
        )

    def test_create_settings_file(self):
        project = Project.objects.filter(name="test-project").first()

        proj_settings = dict()
        proj_settings['auth_url'] = os.path.join('https://' + settings.DOMAIN, 'api/api-token-auth')
        proj_settings['access_key'] = project.project_key
        proj_settings['username'] = "admin"
        proj_settings['token'] = "api_token"
        proj_settings['so_domain_name'] = settings.DOMAIN

        proj_settings['Project'] = dict()
        proj_settings['Project']['project_name'] = project.name
        proj_settings['Project']['project_slug'] = project.slug

        self.assertEqual(create_settings_file(project, "admin", "api_token"), yaml.dump(proj_settings))
