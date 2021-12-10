from logging import raiseExceptions
import secrets
import string

from .exceptions import ProjectCreationException
from .models import Flavor, Environment, Project, S3, MLFlow
from apps.models import Apps, AppInstance
import apps.views as appviews
import apps.tasks as apptasks
from celery import shared_task
from django.conf import settings


@shared_task
def create_resources_from_template(user, project_slug, template):
    print("Create Resources From Project Template...")
    alphabet = string.ascii_letters + string.digits
    project = Project.objects.get(slug=project_slug)
    print(template)
    for key, item in template.items():
        print("Key {}".format(key)) # TO BE REMOVED
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
                    app = Apps.objects.filter(slug=item['app']).order_by('-revision')[0]
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
                    item['credentials.access_key'] = ''.join(secrets.choice(alphabet) for i in range(8))
                if 'credentials.secret_key' in item:
                    item['credentials.secret_key'] = ''.join(secrets.choice(alphabet) for i in range(14))
                if 'credentials.username' in item:
                    item['credentials.username'] = 'admin'
                if 'credentials.password' in item:
                    item['credentials.password'] = ''.join(secrets.choice(alphabet) for i in range(14))
                
                data = {**data, **item}
                print("DATA TEMPLATE")
                print(data)

                res = appviews.create([], user, project.slug, app_slug=item['slug'], data=data, wait=True)

        elif 'settings' == key:
            print("PARSING SETTINGS")
            print("Settings: {}".format(settings))
            if 'project-S3' in item:
                print("SETTING DEFAULT S3")
                s3storage=item['project-S3']
                s3obj = S3.objects.get(name=s3storage, project=project) # Add logics: here it is referring to minio basically. It is assumed that minio exist, but if it doesn't then it blows up of course
                project.s3storage = s3obj
                project.save()
            if 'project-MLflow' in item:
                print("SETTING DEFAULT MLflow")
                mlflow=item['project-MLflow']
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
