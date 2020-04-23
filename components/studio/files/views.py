from django.shortcuts import render
from projects.models import Project
from .helpers import *
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def index(request, user, project, document_root=settings.GIT_REPOS_ROOT):
    template = 'files_list.html'

    project = Project.objects.filter(slug=project).first()

    files = []
    dirs = []
    url = 'http://{}-file-controller/'.format(project.slug)
    import requests as r
    try:
        response = r.get(url)
        if response.status_code == 200 or response.status_code == 203:
            payload = response.json()
            if payload['status'] == 'OK':
                files = payload['files']
                dirs = payload['dirs']
                dirs_temp = list()
                for d in dirs:
                    if str(d['name']).startswith('.'):
                        continue
                    dirs_temp.append(d)
                dirs = dirs_temp
    except Exception as e:
        logger.error("Failed to get response from {} with error: {}".format(url, e))

    return render(request, template, locals())
