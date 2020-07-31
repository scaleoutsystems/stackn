import os
from django.conf import settings

base_dir = settings.GIT_REPOS_ROOT

import logging

logger = logging.getLogger(__file__)

from pathlib import Path

def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)

def _create_userdir(user):
    path = os.path.join(base_dir, user)

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == 17:
            logger.warning("User already created")
            return False


def _safe_to_create(path):
    if os.path.exists(path) and os.path.isdir(path):
        if not os.listdir(path):
            return True
            # print("Directory is empty")
        else:
            return False
            # print("Directory is not empty")
    else:
        return True
        # print("Given Directory don't exists")


def create_repository(user, repository, git_init=True):
    _create_userdir(user)
    path = os.path.join(base_dir, user, repository, ".git")

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == 17:
            logger.warning("Directory already exist")
            return False

    from git import Repo

    if _safe_to_create(path) and git_init:
        try:
            repo = Repo.init(path, bare=True)
        except Exception as e:
            logger.error("Could not initialize a bare git repository")
            return False

    _set_permissions(os.path.join(base_dir, user))

    return True

def _set_permissions(path):
    import os
    try:
        for root, dirs, files in os.walk(path):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o0777)
            for f in files:
                os.chmod(os.path.join(root, f), 0o0777)
    except Exception as e:
        print("Failed to set permissions! {}".format(e))

def delete_repository(user, repository):
    pass
