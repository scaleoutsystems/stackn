from celery import shared_task
import requests as r
import yaml
import base64
import collections
import json
import time

import modules.keycloak_lib as keylib

from .exceptions import ProjectCreationException

from django.conf import settings

from .models import Flavor, Environment, Project, S3





@shared_task
def create_keycloak_client_task(project_slug, username, repository):
    # Create Keycloak client for project with default project role.
    # The creator of the project assumes all roles by default.
    print('Creating Keycloak resources.')
    HOST = settings.DOMAIN
    RELEASE_NAME = str(project_slug)
    # This is just a dummy URL -- it doesn't go anywhere.
    URL = 'https://{}/{}/{}'.format(HOST, username, RELEASE_NAME)

    
    client_id, client_secret, res_json = keylib.keycloak_setup_base_client(URL, RELEASE_NAME, username, settings.PROJECT_ROLES, settings.PROJECT_ROLES)
    if not res_json['success']:
        print("ERROR: Failed to create keycloak client for project.")
    else:
        print('Done creating Keycloak client for project.')


def create_settings_file(project_slug):
    proj_settings = dict()
       
    proj_settings['active'] = 'stackn'
    proj_settings['client_id'] = 'studio-api'
    proj_settings['realm'] = settings.KC_REALM
    proj_settings['active_project'] = project_slug

    return yaml.dump(proj_settings)



@shared_task
def create_resources_from_template(user, project_slug, template):
    from apps.models import Apps
    import apps.views as appviews

    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    template = decoder.decode(template)
    print(template)
    project = Project.objects.get(slug=project_slug)

    if 'flavors' in template:
        flavors = template['flavors']
        for key, item in flavors.items():
            flavor = Flavor(name=key,
                            cpu_req=item['cpu']['requirement'],
                            cpu_lim=item['cpu']['limit'],
                            mem_req=item['mem']['requirement'],
                            mem_lim=item['mem']['limit'],
                            gpu_req=item['gpu']['requirement'],
                            gpu_lim=item['gpu']['limit'],
                            ephmem_req=item['ephmem']['requirement'],
                            ephmem_lim=item['ephmem']['limit'],
                            project=project)
            flavor.save()
    if 'environments' in template:
        environments = template['environments']
        for key, item in environments.items():
            app = Apps.objects.get(slug=item['app'])
            environment = Environment(name=key,
                                      project=project,
                                      repository=item['repository'],
                                      image=item['image'],
                                      app=app)
            environment.save()
    
    if 'apps' in template:
        apps = template['apps']
        for key, item in apps.items():
            app_name = key
            data = {
                "app_name": app_name,
                "app_action": "Create"
            }
            data = {**data, **item}
            print("DATA TEMPLATE")
            print(data)
            res = appviews.create([], user, project.slug, app_slug=item['slug'], data=data, wait=True)

    if 'settings' in template:
        print("PARSING SETTINGS")
        if 'project-S3' in template['settings']:
            print("SETTING DEFAULT S3")
            s3storage=template['settings']['project-S3']
            s3obj = S3.objects.get(name=s3storage, project=project)
            project.s3storage = s3obj
            project.save()
