import time
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, Subquery
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, redirect, render, reverse
from django.template import engines
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from guardian.decorators import permission_required_or_403

from projects.models import Environment, Flavor, Project, ReleaseName

from .generate_form import generate_form
from .helpers import create_instance_params
from .models import AppCategories, AppInstance, AppPermission, Apps, AppStatus
from .serialize import serialize_app
from .tasks import delete_resource, deploy_resource


def get_status_defs():
    status_success = settings.APPS_STATUS_SUCCESS
    status_warning = settings.APPS_STATUS_WARNING
    return status_success, status_warning


# Create your views here.
# TODO: Is this view used?
@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def index(request, user, project):
    print("hello")
    category = 'store'
    template = 'index_apps.html'

    cat_obj = AppCategories.objects.get(slug=category)
    apps = Apps.objects.filter(category=cat_obj)
    project = Project.objects.get(slug=project)
    appinstances = AppInstance.objects.filter(Q(owner=request.user) | Q(
        permission__projects__slug=project.slug) | Q(permission__public=True), app__category=cat_obj)

    return render(request, template, locals())


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def logs(request, user, project, ai_id):
    template = "logs.html"
    app = AppInstance.objects.get(pk=ai_id)
    project = Project.objects.get(slug=project)
    app_settings = app.app.settings
    containers = []
    logs = []
    if 'logs' in app_settings:
        containers = app_settings['logs']
        container = containers[0]
        print("default container: "+container)
        if 'container' in request.GET:
            container = request.GET.get('container')
            print("Got container in request: "+container)

        try:
            url = settings.LOKI_SVC+'/loki/api/v1/query_range'
            app_params = app.parameters
            print('{container="'+container +
                  '",release="'+app_params['release']+'"}')
            query = {
                'query': '{container="'+container+'",release="'+app_params['release']+'"}',
                'limit': 50,
                'start': 0,
            }
            res = requests.get(url, params=query)
            res_json = res.json()['data']['result']

            for item in res_json:
                logs.append('----------BEGIN CONTAINER------------')
                logline = ''
                for iline in item['values']:
                    logs.append(iline[1])
                logs.append('----------END CONTAINER------------')

        except Exception as e:
            print(e)

    return render(request, template, locals())


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def filtered(request, user, project, category):
    # template = 'index_apps.html'
    projects = Project.objects.filter(Q(owner=request.user) | Q(
        authorized=request.user), status='active')
    status_success, status_warning = get_status_defs()
    menu = dict()

    template = 'new.html'
    import django.core.exceptions as ex
    try:
        cat_obj = AppCategories.objects.get(slug=category)
    except ex.ObjectDoesNotExist:
        print("No apps are loaded.")
        cat_obj = []
    menu[category] = 'active'
    media_url = settings.MEDIA_URL
    project = Project.objects.get(slug=project)
    try:
        apps = Apps.objects.filter(pk__in=Subquery(
            Apps.objects.filter((Q(access="public") | Q(projects__in=[project])), category=cat_obj).order_by(
                'slug', '-revision').distinct('slug').values('pk')
        )).order_by('-priority')
    except Exception as err:
        print(err)

    time_threshold = datetime.now() - timedelta(minutes=5)
    print(time_threshold)
    appinstances = AppInstance.objects.filter(
        Q(owner=request.user) | Q(permission__projects__slug=project.slug) | Q(
            permission__public=True),
        ~Q(state='Deleted') | Q(deleted_on__gte=time_threshold),
        app__category=cat_obj,
        project=project).order_by('-created_on')
    pk_list = ''
    for instance in appinstances:
        pk_list += str(instance.pk)+','
    pk_list = pk_list[:-1]
    pk_list = "'"+pk_list+"'"
    apps_installed = False
    if appinstances:
        apps_installed = True

    return render(request, template, locals())


@csrf_exempt
def get_status(request, user, project):
    status_success, status_warning = get_status_defs()
    print("GET_STATUS")
    print(request.POST)
    pk = request.POST.get('pk')
    # print(pk)
    pk = pk.split(',')
    print(pk)
    res = {}
    if len(pk) > 0 and not (len(pk) == 1 and pk[0] == ''):
        appinstances = AppInstance.objects.filter(pk__in=pk)
        print(appinstances)
        res = dict()
        for instance in appinstances:
            try:
                status = instance.status.latest().status_type

            except:
                status = instance.state
            if status in status_success:
                span_class = 'bg-success'
            elif status in status_warning:
                span_class = 'bg-warning'
            else:
                span_class = 'bg-danger'
            res['status-{}'.format(instance.pk)
                ] = '<span class="badge {}">{}</span>'.format(span_class, status)
            print(status)
        print(pk)
    return JsonResponse(res)
    # if 'pk' in request.POST:
    #     pk = request.POST['pk']
    #     appinstances = AppInstance.objects.filter(pk__in=pk)
    #     print(appinstances)


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def appsettings(request, user, project, ai_id):
    all_tags = AppInstance.tags.tag_model.objects.all()
    template = 'create.html'
    app_action = "Settings"

    if 'from' in request.GET:
        from_page = request.GET.get('from')
    else:
        from_page = 'filtered'

    project = Project.objects.get(slug=project)
    appinstance = AppInstance.objects.get(pk=ai_id)
    existing_app_name = appinstance.name
    app = appinstance.app

    aset = appinstance.app.settings
    form = generate_form(aset, project, app, request.user, appinstance)
    return render(request, template, locals())


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def add_tag(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    if request.method == 'POST':
        new_tag = request.POST.get('tag', '')
        print("New Tag: ", new_tag)
        appinstance.tags.add(new_tag)
        appinstance.save()

    return HttpResponseRedirect(reverse('apps:appsettings', kwargs={'user': user, 'project': project, 'ai_id': ai_id}))


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def remove_tag(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    if request.method == 'POST':
        print(request.POST)
        new_tag = request.POST.get('tag', '')
        print("Remove Tag: ", new_tag)
        appinstance.tags.remove(new_tag)
        appinstance.save()

    return HttpResponseRedirect(reverse('apps:appsettings', kwargs={'user': user, 'project': project, 'ai_id': ai_id}))


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def create(request, user, project, app_slug, data=[], wait=False, call=False):
    template = 'create.html'
    app_action = "Create"

    if not call:
        user = request.user
        if 'from' in request.GET:
            from_page = request.GET.get('from')
        else:
            from_page = 'filtered'
    else:
        from_page = ''
        user = User.objects.get(username=user)

    project = Project.objects.get(slug=project)
    app = Apps.objects.filter(slug=app_slug).order_by('-revision')[0]
    app_sett = app.settings

    # Set up form
    print("CREATING APP...")
    print("GENERATING FORM")
    form = generate_form(app_sett, project, app, user, [])
    print("FORM GENERATED: {}".format(form))
    if data or request.method == "POST":
        if not data:
            data = request.POST
        app_name = data.get('app_name')
        parameters_out, app_deps, model_deps = serialize_app(
            data, project, app_sett, user.username)

        if data.get('app_action') == "Create":
            permission = AppPermission(name=app_name)
            permission.save()
        elif data.get('app_action') == "Settings":
            app_instance = AppInstance.objects.get(pk=data.get('app_id'))
            permission = app_instance.permission
        else:
            print("No action set, aborting...")
            print(data.get('app_action'))
            return JsonResponse({'status': 'failed', 'reason': 'app_action not set.'})
        permission.public = False
        permission.projects.set([])
        permission.users.set([])

        access = ""

        if parameters_out['permissions']['public']:
            permission.public = True
            access = "public"
        elif parameters_out['permissions']['project']:
            print("PROJECT PERMISSIONS")
            client_id = project.slug
            access = "project"

            if not 'project' in parameters_out:
                parameters_out['project'] = dict()

            parameters_out['project']['client_id'] = client_id
            parameters_out['project']['client_secret'] = client_id
            parameters_out['project']['slug'] = project.slug
            parameters_out['project']['name'] = project.name
            permission.projects.set([project])
        elif parameters_out['permissions']['private']:
            access = "private"
            permission.users.set([user])
        permission.save()

        if data.get('app_action') == "Create":
            app_instance = AppInstance(name=app_name, access=access, app=app, project=project, info={},
                                       parameters=parameters_out, owner=user)

            create_instance_params(app_instance, "create")

            # Attempt to create a ReleaseName model object
            rel_name_obj = []
            if 'app_release_name' in data and data.get('app_release_name') != '':
                submitted_rn = data.get('app_release_name')
                try:
                    rel_name_obj = ReleaseName.objects.get(
                        name=submitted_rn, project=project, status='active')
                    rel_name_obj.status = 'in-use'
                    rel_name_obj.save()
                    app_instance.parameters['release'] = submitted_rn
                except Exception as e:
                    print("Error: Submitted release name is not owned by project.")
                    print(e)
                    return HttpResponseRedirect(
                        reverse('projects:details', kwargs={'user': request.user, 'project_slug': str(project.slug)}))

            # Add fields for apps table: to be displayed as app details in views
            if app_instance.app.table_field and app_instance.app.table_field != "":
                django_engine = engines['django']
                info_field = django_engine.from_string(
                    app_instance.app.table_field).render(app_instance.parameters)
                app_instance.table_field = eval(info_field)
            else:
                app_instance.table_field = {}

            # Setting status fields before saving app instance
            status = AppStatus(appinstance=app_instance)
            status.status_type = 'Created'
            status.info = app_instance.parameters['release']
            app_instance.save()
            # Saving ReleaseName, permissions, status and setting up dependencies
            if rel_name_obj:
                rel_name_obj.app = app_instance
                rel_name_obj.save()
            status.save()
            permission.appinstance = app_instance
            permission.save()
            app_instance.app_dependencies.set(app_deps)
            app_instance.model_dependencies.set(model_deps)

            # Finally, attempting to create apps resources
            res = deploy_resource.delay(app_instance.pk, "create")

            # wait is passed as a function parameter
            if wait:
                while not res.ready():
                    time.sleep(0.1)

            # End of Create action
        elif data.get('app_action') == "Settings":
            print("UPDATING APP DEPLOYMENT")
            app_instance.name = app_name
            app_instance.parameters.update(parameters_out)
            app_instance.save()
            app_instance.app_dependencies.set(app_deps)
            app_instance.model_dependencies.set(model_deps)
            # Attempting to deploy apps settings
            res = deploy_resource.delay(app_instance.pk, "update")
        else:
            raise Exception("Incorrect action on app.")

        # Forming a final response
        if request:
            if 'from' in request.GET:
                from_page = request.GET.get('from')
                if from_page == "overview":
                    return HttpResponseRedirect(
                        reverse('projects:details', kwargs={'user': request.user, 'project_slug': str(project.slug)}))
                elif from_page == "filtered":
                    return HttpResponseRedirect(
                        reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': app_instance.app.category.slug}))
            else:
                return HttpResponseRedirect(
                    reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project.slug), 'category': app_instance.app.category.slug}))
        else:
            return JsonResponse({"status": "ok"})
    # If not POST, thus GET...
    return render(request, template, locals())


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def publish(request, user, project, category, ai_id):
    print("Publish app {}".format(ai_id))
    print(project)
    try:
        app = AppInstance.objects.get(pk=ai_id)
        print(app)
        # TODO: Check that user is allowed to publish this app.
        print("setting public")
        if app.access == "private":
            app.access = "public"
        else:
            app.access = "private"
        print("saving")
        app.save()
        print("done")
    except Exception as err:
        print(err)

    return HttpResponseRedirect(
        reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))


@permission_required_or_403('can_view_project',
                            (Project, 'slug', 'project'))
def delete(request, user, project, category, ai_id):
    print("PK="+str(ai_id))

    if 'from' in request.GET:
        from_page = request.GET.get('from')
    else:
        from_page = 'filtered'

    delete_resource.delay(ai_id)

    if 'from' in request.GET:
        from_page = request.GET.get('from')
        if from_page == "overview":
            return HttpResponseRedirect(
                reverse('projects:details', kwargs={'user': request.user, 'project_slug': str(project)}))
        elif from_page == "filtered":
            return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))
        else:
            return HttpResponseRedirect(
                reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))

    return HttpResponseRedirect(
        reverse('apps:filtered', kwargs={'user': request.user, 'project': str(project), 'category': category}))
