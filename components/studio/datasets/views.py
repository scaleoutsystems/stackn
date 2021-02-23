from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseRedirect
from projects.models import Project
from studio.minio import MinioRepository, ResponseError
from django.conf import settings as sett
from projects.helpers import get_minio_keys
from .forms import DatasheetForm


@login_required
def page(request, user, project):
    template = 'dataset_page.html'
    project = Project.objects.get(slug=project)
    url_domain = sett.DOMAIN

    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

    datasets = []
    try:
        minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), decrypted_key,
                                           decrypted_secret)

        objects = minio_repository.client.list_objects_v2('dataset', recursive=True)
        for obj in objects:
            datasets.append({'name': obj.object_name,
                             'datasheet': 'datasheet',
                             'size': round(obj.size / 1000000, 2),
                             'location': 'minio',
                             'modified': obj.last_modified})
    except ResponseError as err:
        print(err)

    return render(request, template, locals())


@login_required
def datasheet(request, user, project, page_index):
    template = 'dataset_datasheet.html'
    project = Project.objects.filter(slug=project).first()
    url_domain = sett.DOMAIN

    minio_keys = get_minio_keys(project)
    decrypted_key = minio_keys['project_key']
    decrypted_secret = minio_keys['project_secret']

    submitbutton = request.POST.get("submit")

    datasheet_info = []

    form = DatasheetForm(request.POST or None)
    if form.is_valid():
        datasheet_info.append(form.cleaned_data.get("q1"))
        datasheet_info.append(form.cleaned_data.get("q2"))
        print(datasheet_info)

    datasets = []
    try:
        minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), decrypted_key,
                                           decrypted_secret)

        objects = minio_repository.client.list_objects_v2('dataset')
        for obj in objects:
            datasets.append({'is_dir': obj.is_dir,
                             # remove '/' after the directory name
                             'name': obj.object_name[:-1] if obj.is_dir else obj.object_name,
                             'datasheet': 'datasheet',
                             'size': round(obj.size / 1000000, 2),
                             'location': 'minio',
                             'modified': obj.last_modified})
    except ResponseError as err:
        print(err)

    previous_page = 1
    next_page = 1
    if len(datasets) > 0:
        import math
        # allow 10 rows per page in the table
        pages = list(map(lambda x: x + 1, range(math.ceil(len(datasets) / 10))))

        datasets = datasets[page_index * 10 - 10:page_index * 10]

        previous_page = page_index if page_index == 1 else page_index - 1
        next_page = page_index if page_index == pages[-1] else page_index + 1

    return render(request, template, locals())
