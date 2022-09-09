from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from guardian.shortcuts import assign_perm, remove_perm

from projects.models import Project

from .models import AppInstance, Apps

User = get_user_model()

class AppsViewForbidden(TestCase):
    def setUp(self):
        user = User.objects.create_user('foo', 'foo@test.com', 'bar')

        project = Project.objects.create_project(
            name='test-perm',
            owner=user,
            description='',
            repository=''
        )

        user = User.objects.create_user("member", 'foo@test.com', 'bar')
        self.client.login(username='member', password='bar')

    def test_forbidden_apps_compute(self):
        """
        Test non-project member not allowed to access /<category>=compute
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:filtered',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'category': 'compute'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_serve(self):
        """
        Test non-project member not allowed to access /<category>=serve
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:filtered',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'category': 'serve'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_store(self):
        """
        Test non-project member not allowed to access /<category>=store
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:filtered',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'category': 'store'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_develop(self):
        """
        Test non-project member not allowed to access /<category>=develop
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:filtered',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'category': 'develop'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_create(self):
        """
        Test non-project member not allowed to access /create/<app_slug>=test
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:create',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'app_slug': 'test'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_logs(self):
        """
        Test non-project member not allowed to access /logs/<ai_id>=1
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:logs',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'ai_id': '1'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_settings(self):
        """
        Test non-project member not allowed to access /seetings/<ai_id>=1
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:appsettings',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'ai_id': '1'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_settings_add_tag(self):
        """
        Test non-project member not allowed to access /settings/<ai_id>=1/add_tag
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:add_tag',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'ai_id': '1'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_settings_remove_tag(self):
        """
        Test non-project member not allowed to access /settings/<ai_id>=1/remove_tag
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:remove_tag',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'ai_id': '1'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_delete(self):
        """
        Test non-project member not allowed to access /delete/<category>=compute/<ai_id>=1
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:delete',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'ai_id': '1',
                    'category': 'compute'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)

    def test_forbidden_apps_publish(self):
        """
        Test non-project member not allowed to access /publish/<category>=compute/<ai_id>=1
        """
        owner = User.objects.get(username='foo')
        project = Project.objects.get(name='test-perm')
        response = self.client.get(
            reverse(
                'apps:publish',
                kwargs={
                    'user': owner,
                    'project': project.slug,
                    'ai_id': '1',
                    'category': 'compute'
                }
            )
        )
        self.assertTemplateUsed(response, '403.html')
        self.assertEqual(response.status_code, 403)
