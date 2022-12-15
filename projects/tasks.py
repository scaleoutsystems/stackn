import collections
import json
import secrets
import string
from logging import raiseExceptions

from celery import shared_task
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest

import apps.tasks as apptasks
import apps.views as appviews
from apps.controller import delete


from .exceptions import ProjectCreationException
from .models import S3, Environment, Flavor, MLFlow, Project

Apps = apps.get_model(app_label=settings.APPS_MODEL)
AppInstance = apps.get_model(app_label=settings.APPINSTANCE_MODEL)

User = get_user_model()


@shared_task
def create_resources_from_template(user, project_slug, template):
    print("Create Resources From Project Template...")
    decoder = json.JSONDecoder(object_pairs_hook=collections.OrderedDict)
    parsed_template = template.replace('\'', '\"')
    template = decoder.decode(parsed_template)
    alphabet = string.ascii_letters + string.digits
    project = Project.objects.get(slug=project_slug)
    print("Parsing template...")
    for key, item in template.items():
        print("Key {}".format(key))
        if 'flavors' == key:
            flavors = item
            print("Flavors: {}".format(flavors))
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
        elif 'environments' == key:
            environments = item
            print("Environments: {}".format(environments))
            for key, item in environments.items():
                try:
                    app = Apps.objects.filter(
                        slug=item['app']).order_by('-revision')[0]
                except Exception as err:
                    print("App for environment not found.")
                    print(item['app'])
                    print(project_slug)
                    print(user)
                    print(err)
                    raise
                try:
                    environment = Environment(name=key,
                                              project=project,
                                              repository=item['repository'],
                                              image=item['image'],
                                              app=app)
                    environment.save()
                except Exception as err:
                    print("Failed to create new environment: {}".format(key))
                    print(project)
                    print(item['repository'])
                    print(item['image'])
                    print(app)
                    print(user)
                    print(err)
        elif 'apps' == key:
            apps = item
            print("Apps: {}".format(apps))
            for key, item in apps.items():
                app_name = key
                data = {
                    "app_name": app_name,
                    "app_action": "Create"
                }
                if 'credentials.access_key' in item:
                    item['credentials.access_key'] = ''.join(
                        secrets.choice(alphabet) for i in range(8))
                if 'credentials.secret_key' in item:
                    item['credentials.secret_key'] = ''.join(
                        secrets.choice(alphabet) for i in range(14))
                if 'credentials.username' in item:
                    item['credentials.username'] = 'admin'
                if 'credentials.password' in item:
                    item['credentials.password'] = ''.join(
                        secrets.choice(alphabet) for i in range(14))

                data = {**data, **item}
                print("DATA TEMPLATE")
                print(data)
                request = HttpRequest()
                request.user = User.objects.get(username=user)
                res = appviews.create(request=request, user=user, project=project.slug,
                                      app_slug=item['slug'], data=data, wait=True, call=True)

        elif 'settings' == key:
            print("PARSING SETTINGS")
            print("Settings: {}".format(settings))
            if 'project-S3' in item:
                print("SETTING DEFAULT S3")
                s3storage = item['project-S3']
                # Add logics: here it is referring to minio basically. It is assumed that minio exist, but if it doesn't then it blows up of course
                s3obj = S3.objects.get(name=s3storage, project=project)
                project.s3storage = s3obj
                project.save()
            if 'project-MLflow' in item:
                print("SETTING DEFAULT MLflow")
                mlflow = item['project-MLflow']
                mlflowobj = MLFlow.objects.get(name=mlflow, project=project)
                project.mlflow = mlflowobj
                project.save()
        else:
            print("Template has either not valid or unknown keys")
            raise(ProjectCreationException)


@shared_task
def delete_project_apps(project_slug):
    project = Project.objects.get(slug=project_slug)
    apps = AppInstance.objects.filter(project=project)
    for app in apps:
        apptasks.delete_resource.delay(app.pk)


@shared_task
def delete_project(project):
    print("SCHEDULING DELETION OF ALL INSTALLED APPS")
    delete_project_apps_permanently(project)

    project.delete()

@shared_task
def delete_project_apps_permanently(project):
    
    apps = AppInstance.objects.filter(project=project)
    
    for app in apps:
        helm_output = delete(app.parameters)
        print(helm_output.stderr.decode('utf-8'))