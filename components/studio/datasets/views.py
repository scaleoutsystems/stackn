from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseRedirect
from projects.models import Project
from studio.minio import MinioRepository
from minio import Minio
from django.conf import settings as sett
from projects.helpers import get_minio_keys


@login_required
def page(request, user, project):
    template = 'dataset_page.html'
    project = Project.objects.get(slug=project)
    url_domain = sett.DOMAIN

    # minio_keys = get_minio_keys(project)
    # decrypted_key = minio_keys['project_key']
    # decrypted_secret = minio_keys['project_secret']

    datasets = []
    try:
        host = project.s3storage.host
        access_key = project.s3storage.access_key
        secret_key = project.s3storage.secret_key
        minio_repository = Minio(host.strip('/'), access_key, secret_key)
        objects = minio_repository.list_objects('dataset', recursive=True)
        for obj in objects:
            datasets.append({'name': obj.object_name,
                             'datasheet': 'datasheet',
                             'size': round(obj.size / 1000000, 2),
                             'location': 'minio',
                             'modified': obj.last_modified})
    except Exception as err:
        print(err)

    return render(request, template, locals())
