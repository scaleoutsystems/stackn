from .exceptions import ProjectCreationException
from django.conf import settings
import requests as r
from .models import Environment
from .jobs import load_definition, start_job


def create_project_resources(project, repository=None):
    create_environment_image(project, repository)
    create_helm_resources(project, repository)


def create_environment_image(project, repository=None):

    if project.environment:
        definition = load_definition(project)
        start_job(definition)


def create_helm_resources(project, repository=None):

    parameters = {'release': str(project.slug),
                  'chart': 'project',
                  'minio.access_key': project.project_key,
                  'minio.secret_key': project.project_secret,
                  'global.domain': settings.DOMAIN,
                  'storageClassName': settings.STORAGECLASS}
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

