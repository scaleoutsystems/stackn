import os
import pathlib
import shutil
from django.test import TestCase
from django.contrib.auth.models import User
from django.conf import settings
from .helpers import _create_userdir, _safe_to_create, create_repository

base_dir = settings.GIT_REPOS_ROOT


class FilesTestCase(TestCase):
    def setUp(self):
        User.objects.create_user(username="admin")

    def test__create_userdir(self):
        user = User.objects.filter(username="admin").first()
        path = os.path.join(base_dir, user.username)

        _create_userdir(user.username)

        self.assertEqual(os.path.isdir(path), True)
        self.assertEqual(_create_userdir(user.username), False)

        os.rmdir(path)

    def test__safe_to_create(self):
        path = os.path.join(base_dir, "test__safe_to_create")
        os.makedirs(path)

        self.assertEqual(_safe_to_create(path), True)

        os.rmdir(path)

        self.assertEqual(_safe_to_create(path), True)

        path = pathlib.Path(__file__).parent.absolute()

        self.assertNotEqual(_safe_to_create(path), True)

    def test_create_repository(self):
        user = User.objects.filter(username="admin").first()

        result = create_repository(user.username, "test_create_repository")

        path = os.path.join(base_dir, user.username, "test_create_repository", ".git")
        self.assertEqual(os.path.isdir(path), True)
        self.assertEqual(result, True)

        path = os.path.join(base_dir, user.username)
        shutil.rmtree(path)
