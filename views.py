from datetime import datetime, timedelta
from json import load

import django.core.exceptions as ex
import requests
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Subquery
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import HttpResponseRedirect, render, reverse
from django.utils.decorators import method_decorator
from django.views import View
from guardian.decorators import permission_required_or_403

from .generate_form import generate_form
from .helpers import create_app_instance, handle_permissions
from .models import AppCategories, AppInstance, Apps
from .serialize import serialize_app
from .tasks import delete_resource, deploy_resource

Project = apps.get_model(app_label=settings.PROJECTS_MODEL)
ReleaseName = apps.get_model(app_label=settings.RELEASENAME_MODEL)

User = get_user_model()


def get_status_defs():
    status_success = settings.APPS_STATUS_SUCCESS
    status_warning = settings.APPS_STATUS_WARNING
    return status_success, status_warning


# Create your views here.
# TODO: Is this view used?
@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def index(request, user, project):
    print("hello")
    category = "store"
    template = "index_apps.html"

    cat_obj = AppCategories.objects.get(slug=category)
    apps = Apps.objects.filter(category=cat_obj)
    project = Project.objects.get(slug=project)
    appinstances = AppInstance.objects.filter(
        Q(owner=request.user)
        | Q(permission__projects__slug=project.slug)
        | Q(permission__public=True),
        app__category=cat_obj,
    )

    return render(request, template, locals())


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def logs(request, user, project, ai_id):
    template = "logs.html"
    app = AppInstance.objects.get(pk=ai_id)
    project = Project.objects.get(slug=project)
    app_settings = app.app.settings
    containers = []
    logs = []
    if "logs" in app_settings:
        containers = app_settings["logs"]
        container = containers[0]
        print("default container: " + container)
        if "container" in request.GET:
            container = request.GET.get("container")
            print("Got container in request: " + container)

        try:
            url = settings.LOKI_SVC + "/loki/api/v1/query_range"
            app_params = app.parameters
            print(
                '{container="'
                + container
                + '",release="'
                + app_params["release"]
                + '"}'
            )
            query = {
                "query": '{container="'
                + container
                + '",release="'
                + app_params["release"]
                + '"}',
                "limit": 50,
                "start": 0,
            }
            res = requests.get(url, params=query)
            res_json = res.json()["data"]["result"]

            for item in res_json:
                logs.append("----------BEGIN CONTAINER------------")
                logline = ""
                for iline in item["values"]:
                    logs.append(iline[1])
                logs.append("----------END CONTAINER------------")

        except Exception as e:
            print(e)

    return render(request, template, locals())


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def filtered(request, user, project, category):
    # template = 'index_apps.html'
    projects = Project.objects.filter(
        Q(owner=request.user) | Q(authorized=request.user), status="active"
    )
    status_success, status_warning = get_status_defs()
    menu = dict()

    template = "new.html"

    try:
        cat_obj = AppCategories.objects.get(slug=category)
    except ex.ObjectDoesNotExist:
        print("No apps are loaded.")
        cat_obj = []
    menu[category] = "active"
    media_url = settings.MEDIA_URL
    project = Project.objects.get(slug=project)
    try:
        apps = Apps.objects.filter(
            pk__in=Subquery(
                Apps.objects.filter(
                    (Q(access="public") | Q(projects__in=[project])),
                    category=cat_obj,
                    user_can_create=True,
                )
                .order_by("slug", "-revision")
                .distinct("slug")
                .values("pk")
            )
        ).order_by("-priority")
    except Exception as err:
        print(err)

    time_threshold = datetime.now() - timedelta(minutes=5)
    print(time_threshold)
    appinstances = AppInstance.objects.filter(
        Q(owner=request.user) | Q(access__in=["project", "public"]),
        ~Q(state="Deleted") | Q(deleted_on__gte=time_threshold),
        app__category=cat_obj,
        project=project,
    ).order_by("-created_on")
    pk_list = ""
    for instance in appinstances:
        pk_list += str(instance.pk) + ","
    pk_list = pk_list[:-1]
    pk_list = "'" + pk_list + "'"
    apps_installed = False
    if appinstances:
        apps_installed = True

    return render(request, template, locals())


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def get_status(request, user, project):
    if request.method == "POST":
        status_success, status_warning = get_status_defs()
        app_pks = load(request)
        arr = app_pks.split(",")

        if len(arr) > 0 and not (len(arr) == 1 and arr[0] == ""):
            app_instances = AppInstance.objects.filter(pk__in=arr)

            result = {}

            for instance in app_instances:
                try:
                    status = instance.status.latest().status_type
                except:  # noqa E722 TODO: Add exception
                    status = instance.state

                status_group = (
                    "success"
                    if status in status_success
                    else "warning"
                    if status in status_warning
                    else "danger"
                )

                obj = {
                    "status": status,
                    "statusGroup": status_group,
                }

                result[f"{instance.pk}"] = obj

            return JsonResponse(result)

    return HttpResponseNotFound("<h1>Page not found</h1>")


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project")
    ),
    name="dispatch",
)
class AppSettingsView(View):
    def get_shared_data(self, project_slug, ai_id):
        project = Project.objects.get(slug=project_slug)
        appinstance = AppInstance.objects.get(pk=ai_id)

        return [project, appinstance]

    def get(self, request, user, project, ai_id):
        project, appinstance = self.get_shared_data(project, ai_id)

        all_tags = AppInstance.tags.tag_model.objects.all()
        template = "update.html"
        show_permissions = True
        from_page = (
            request.GET.get("from") if "from" in request.GET else "filtered"
        )
        existing_app_name = appinstance.name
        app = appinstance.app
        app_settings = appinstance.app.settings
        form = generate_form(
            app_settings, project, app, request.user, appinstance
        )

        if request.user.id != appinstance.owner.id:
            show_permissions = False

        return render(request, template, locals())

    def post(self, request, user, project, ai_id):
        project, appinstance = self.get_shared_data(project, ai_id)

        app = appinstance.app
        app_settings = app.settings
        body = request.POST.copy()

        if not body.get("permission", None):
            body.update({"permission": appinstance.access})

        parameters, app_deps, model_deps = serialize_app(
            body, project, app_settings, request.user.username
        )

        access = handle_permissions(parameters, project)

        appinstance.name = request.POST.get("app_name")
        appinstance.parameters.update(parameters)
        appinstance.access = access
        appinstance.save()
        appinstance.app_dependencies.set(app_deps)
        appinstance.model_dependencies.set(model_deps)
        # Attempting to deploy apps settings
        _ = deploy_resource.delay(appinstance.pk, "update")

        return HttpResponseRedirect(
            reverse(
                "projects:details",
                kwargs={
                    "user": request.user,
                    "project_slug": str(project.slug),
                },
            )
        )


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def add_tag(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    if request.method == "POST":
        new_tag = request.POST.get("tag", "")
        print("New Tag: ", new_tag)
        appinstance.tags.add(new_tag)
        appinstance.save()

    return HttpResponseRedirect(
        reverse(
            "apps:appsettings",
            kwargs={"user": user, "project": project, "ai_id": ai_id},
        )
    )


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def remove_tag(request, user, project, ai_id):
    appinstance = AppInstance.objects.get(pk=ai_id)
    if request.method == "POST":
        print(request.POST)
        new_tag = request.POST.get("tag", "")
        print("Remove Tag: ", new_tag)
        appinstance.tags.remove(new_tag)
        appinstance.save()

    return HttpResponseRedirect(
        reverse(
            "apps:appsettings",
            kwargs={"user": user, "project": project, "ai_id": ai_id},
        )
    )


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project")
    ),
    name="dispatch",
)
class CreateView(View):
    def get_shared_data(self, project_slug, app_slug):
        project = Project.objects.get(slug=project_slug)
        app = Apps.objects.filter(slug=app_slug).order_by("-revision")[0]
        app_settings = app.settings

        return [project, app, app_settings]

    def get(
        self, request, user, project, app_slug, data=[], wait=False, call=False
    ):
        template = "create.html"
        project, app, app_settings = self.get_shared_data(project, app_slug)

        if not call:
            user = request.user
            if "from" in request.GET:
                from_page = request.GET.get("from")
            else:
                from_page = "filtered"
        else:
            from_page = ""
            user = User.objects.get(username=user)

        form = generate_form(app_settings, project, app, user, [])

        return render(request, template, locals())

    def post(self, request, user, project, app_slug, data=[], wait=False):
        project, app, app_settings = self.get_shared_data(project, app_slug)
        data = request.POST
        user = request.user

        if not app.user_can_create:
            raise Exception("User not allowed to create app")

        successful, project_slug, app_category_slug = create_app_instance(
            user, project, app, app_settings, data, wait
        )

        if not successful:
            return HttpResponseRedirect(
                reverse(
                    "projects:details",
                    kwargs={
                        "user": request.user,
                        "project_slug": str(project.slug),
                    },
                )
            )

        if "from" in request.GET:
            from_page = request.GET.get("from")
            if from_page == "overview":
                return HttpResponseRedirect(
                    reverse(
                        "projects:details",
                        kwargs={
                            "user": request.user,
                            "project_slug": str(project_slug),
                        },
                    )
                )

        return HttpResponseRedirect(
            reverse(
                "apps:filtered",
                kwargs={
                    "user": request.user,
                    "project": str(project_slug),
                    "category": app_category_slug,
                },
            )
        )


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def publish(request, user, project, category, ai_id):
    print("Publish app {}".format(ai_id))
    print(project)
    try:
        app = AppInstance.objects.get(pk=ai_id)
        print(app)
        # TODO: Check that user is allowed to publish this app.
        print("setting public")
        app.access = "public"
        print("saving")
        app.save()
        print("done")
    except Exception as err:
        print(err)

    return HttpResponseRedirect(
        reverse(
            "apps:filtered",
            kwargs={
                "user": request.user,
                "project": str(project),
                "category": category,
            },
        )
    )


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def unpublish(request, user, project, category, ai_id):
    try:
        app = AppInstance.objects.get(pk=ai_id)
        app.access = "project"
        app.save()
    except Exception as err:
        print(err)

    return HttpResponseRedirect(
        reverse(
            "apps:filtered",
            kwargs={
                "user": request.user,
                "project": str(project),
                "category": category,
            },
        )
    )


@permission_required_or_403("can_view_project", (Project, "slug", "project"))
def delete(request, user, project, category, ai_id):
    print("PK=" + str(ai_id))

    if "from" in request.GET:
        from_page = request.GET.get("from")
    else:
        from_page = "filtered"

    delete_resource.delay(ai_id)
    # fix: in case appinstance is public swich to private
    app = AppInstance.objects.get(pk=ai_id)
    app.access = "private"
    app.save()

    if "from" in request.GET:
        from_page = request.GET.get("from")
        if from_page == "overview":
            return HttpResponseRedirect(
                reverse(
                    "projects:details",
                    kwargs={
                        "user": request.user,
                        "project_slug": str(project),
                    },
                )
            )
        elif from_page == "filtered":
            return HttpResponseRedirect(
                reverse(
                    "apps:filtered",
                    kwargs={
                        "user": request.user,
                        "project": str(project),
                        "category": category,
                    },
                )
            )
        else:
            return HttpResponseRedirect(
                reverse(
                    "apps:filtered",
                    kwargs={
                        "user": request.user,
                        "project": str(project),
                        "category": category,
                    },
                )
            )

    return HttpResponseRedirect(
        reverse(
            "apps:filtered",
            kwargs={
                "user": request.user,
                "project": str(project),
                "category": category,
            },
        )
    )
