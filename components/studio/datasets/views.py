from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from projects.models import Project
from .forms import DatasetForm
from .models import Dataset
from studio.minio import MinioRepository, ResponseError


@login_required(login_url='/accounts/login')
def index(request, user, project):
    template = 'dataset_index.html'
    project = Project.objects.filter(slug=project).first()

    try:
        minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), project.project_key,
                                           project.project_secret)

        if not minio_repository.client.bucket_exists('dataset'):
            minio_repository.client.make_bucket('dataset')
    except ResponseError as err:
        print(err)

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def create(request, user, project):
    template = 'dataset_create.html'

    if request.method == 'POST':
        project = Project.objects.filter(slug=project).first()
        obj = None
        form = DatasetForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()

            next_page = '/projects/{}/{}/datasets/{}/details'.format(user, project.slug, str(obj.pk))

            return HttpResponseRedirect(next_page)

        next_page = '/projects/{}/{}/datasets/'.format(user, project.slug)

        return HttpResponseRedirect(next_page)
    else:
        project = Project.objects.filter(slug=project).first()
        form = DatasetForm({'project': project.id})

        return render(request, template, locals())


@login_required(login_url='/accounts/login')
def details(request, user, project, id):
    template = 'dataset_details.html'

    project = Project.objects.filter(slug=project).first()
    dataset = Dataset.objects.filter(id=id).first()

    return render(request, template, locals())


@login_required(login_url='/accounts/login')
def page(request, user, project, page_index):
    template = 'dataset_page.html'
    project = Project.objects.filter(slug=project).first()

    datasets = []

    datasets_studio = Dataset.objects.filter(project=project)
    for d in datasets_studio:

        size = 0.0
        try:
            size = round(d.data.size / 1000000, 2)
        except FileNotFoundError as err:
            print(err)

        datasets.append({'is_dir': False,
                         'name': d.data.name,
                         'size': size,
                         'location': 'studio',
                         'modified': d.uploaded_at})

    try:
        minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), project.project_key,
                                           project.project_secret)

        objects = minio_repository.client.list_objects_v2('dataset')
        for obj in objects:
            datasets.append({'is_dir': obj.is_dir,
                             # remove '/' after the directory name
                             'name': obj.object_name[:-1] if obj.is_dir else obj.object_name,
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


@login_required(login_url='/accounts/login')
def path_page(request, user, project, path_name, page_index):
    template = 'dataset_path_page.html'
    project = Project.objects.filter(slug=project).first()

    datasets = []
    try:
        minio_repository = MinioRepository('{}-minio:9000'.format(project.slug), project.project_key,
                                           project.project_secret)

        objects = minio_repository.client.list_objects_v2('dataset', recursive=True)
        for obj in objects:
            if obj.object_name.startswith(path_name + '/'):
                datasets.append({'is_dir': obj.is_dir,
                                 'name': obj.object_name.replace(path_name + '/', ''),
                                 'size': round(obj.size / 1000000, 2),
                                 'modified': obj.last_modified})

        import math
        pages = list(map(lambda x: x + 1, range(math.ceil(len(datasets) / 10))))
    except ResponseError as err:
        print(err)

    datasets = datasets[page_index * 10 - 10:page_index * 10]

    previous_page = page_index if page_index == 1 else page_index - 1
    next_page = page_index if page_index == pages[-1] else page_index + 1

    return render(request, template, locals())
