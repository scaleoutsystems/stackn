from django.test import TestCase
from django.contrib.auth.models import User
from .models import Environment, Project
import os
from django.conf import settings
from .helpers import decrypt_key
from django.urls import reverse
import yaml


class ProjectTestCase(TestCase):
    def setUp(self):
        
        user = User.objects.create_user("admin")
        Project.objects.create(
            name="test-secret",
            slug="test-secret",
            owner=user,
            project_key="a2V5",
            project_secret="c2VjcmV0"
        )
        project = Project.objects.create_project(
            name='test-perm', 
            owner=user, 
            description='', 
            repository=''
        )
        user = User.objects.create_user("member")


    def test_decrypt_key(self):
        project = Project.objects.filter(name="test-secret").first()

        self.assertEqual(decrypt_key(project.project_key), "key")
        self.assertEqual(decrypt_key(project.project_secret), "secret")

    def test_owner_can_view_permission(self):
        project = Project.objects.get(name='test-perm')
        self.assertTrue(project.owner.has_perm('can_view_project', project))

    def test_member_can_view_permission(self):
        user = User.objects.get(username="member")
        project = Project.objects.get(name='test-perm')
        self.assertFalse(user.has_perm('can_view_project', project))



class ProjectViewTestCase(TestCase):
    def setUp(self):
        user = User.objects.create_user('foo', 'test@test.com', 'bar')

    def test_create_project_post(self):
        """
        TODO: Make sure this returns the correct redirect
        """
        self.client.login(username='foo', password='bar')
        response = self.client.post('projects:create')
        self.assertEqual(response.status_code, 302)
    
    def test_create_project_get(self):
        """
        TODO: Make sure this render the /create page for default project template
        """
        self.client.login(username='foo', password='bar')
        response = self.client.get('/create', follow=True)
        self.assertEqual(response.status_code, 200)

