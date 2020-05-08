from .exceptions import ProjectCreationException
from django.conf import settings
import requests as r
import os
import yaml
from .models import Environment
from .jobs import load_definition, start_job

import re

def urlify(s):

    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)

    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '-', s)

    return s

def create_settings_file(project, username, token):
    proj_settings = dict()
    proj_settings['auth_url'] = os.path.join('https://'+settings.DOMAIN, 'api/api-token-auth')
    proj_settings['access_key'] = project.project_key
    proj_settings['username'] = username
    proj_settings['token'] = token
    proj_settings['so_domain_name'] = settings.DOMAIN
    
    proj_settings['Project'] = dict()
    proj_settings['Project']['project_name'] = project.name

    return yaml.dump(proj_settings)

def create_project_resources(project, username, repository=None):
    create_environment_image(project, repository)
    create_helm_resources(project, username, repository)


def create_environment_image(project, repository=None):

    if project.environment:
        definition = load_definition(project)
        start_job(definition)


def create_helm_resources(project, user, repository=None):
    from rest_framework.authtoken.models import Token
    token = Token.objects.get_or_create(user=user)
    proj_settings = create_settings_file(project, user.username, token[0].key)
    # proj_settings = proj_settings.translate(str.maketrans({"'":  r"\'", "]": r"\]", "[":r"\["}))
    parameters = {'release': str(project.slug),
                  'chart': 'project',
                  'minio.access_key': project.project_key,
                  'minio.secret_key': project.project_secret,
                  'global.domain': settings.DOMAIN,
                  'storageClassName': settings.STORAGECLASS,
                  'settings_file': proj_settings}
    if repository:
        parameters.update({'labs.repository': repository})

    url = settings.CHART_CONTROLLER_URL + '/deploy'

    retval = r.get(url, parameters)
    print("CREATE_PROJECT:helm chart creator returned {}".format(retval))

    if retval.status_code >= 200 or retval.status_code < 205:
        return True

    raise ProjectCreationException(__name__)


def delete_project_resources(project):
    retval = r.get(settings.CHART_CONTROLLER_URL + '/delete?release={}'.format(str(project.slug)))

    if retval:
        return True

    return False

