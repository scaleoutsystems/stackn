import base64
import logging

import requests as r
from django.apps import apps
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render, reverse
from django.utils.decorators import method_decorator
from django.views import View
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm, remove_perm

from .exceptions import ProjectCreationException
from .forms import PublishProjectToGitHub
from .models import (
    S3,
    Environment,
    Flavor,
    MLFlow,
    Project,
    ProjectLog,
    ProjectTemplate,
)
from .tasks import create_resources_from_template, delete_project

logger = logging.getLogger(__name__)
Apps = apps.get_model(app_label=django_settings.APPS_MODEL)
AppInstance = apps.get_model(app_label=django_settings.APPINSTANCE_MODEL)
AppCategories = apps.get_model(app_label=django_settings.APPCATEGORIES_MODEL)
Model = apps.get_model(app_label=django_settings.MODELS_MODEL)
User = get_user_model()


class IndexView(View):
    def get(self, request):
        template = "projects/index.html"
        try:
            if request.user.is_superuser:
                projects = Project.objects.filter(status="active").distinct("pk")
            else:
                projects = Project.objects.filter(
                    Q(owner=request.user) | Q(authorized=request.user),
                    status="active",
                ).distinct("pk")
        except TypeError as err:
            projects = []
            print(err)

        request.session["next"] = "/projects/"

        user_can_create = Project.objects.user_can_create(request.user)

        context = {
            "projects": projects,
            "user_can_create": user_can_create,
        }

        return render(request, template, context)


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def settings(request, user, project_slug):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status="active").distinct(
            "pk"
        )
    except TypeError as err:
        projects = []
        print(err)

    template = "projects/settings.html"
    project = Project.objects.filter(
        Q(owner=request.user) | Q(authorized=request.user),
        Q(slug=project_slug),
    ).first()

    try:
        User._meta.get_field("is_user")
        platform_users = User.objects.filter(
            ~Q(pk=project.owner.pk),
            ~Q(username="AnonymousUser"),
            ~Q(username="admin"),
            is_user=True,
        )
    except FieldDoesNotExist:
        platform_users = User.objects.filter(
            ~Q(pk=project.owner.pk),
            ~Q(username="AnonymousUser"),
            ~Q(username="admin"),
        )

    environments = Environment.objects.filter(project=project)
    apps = Apps.objects.all().order_by("slug", "-revision").distinct("slug")

    s3instances = S3.objects.filter(Q(project=project), Q(app__state="Running"))
    flavors = Flavor.objects.filter(project=project)
    mlflows = MLFlow.objects.filter(Q(project=project), Q(app__state="Running"))

    registry_app = Apps.objects.get(slug="docker-registry")
    registries = AppInstance.objects.filter(app=registry_app.pk, project=project)

    return render(request, template, locals())


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project_slug")
    ),
    name="dispatch",
)
class UpdatePatternView(View):
    def validate(self, pattern):
        if pattern is None:
            return False

        _valid_patterns = [f"pattern-{x}" for x in range(1, 31)]

        return pattern in _valid_patterns

    def post(self, request, user, project_slug, *args, **kwargs):
        pattern = request.POST["pattern"]

        valid = self.validate(pattern)

        if valid:
            project = Project.objects.get(slug=project_slug)

            project.pattern = pattern

            project.save()

            return HttpResponse()

        return HttpResponseBadRequest()


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def change_description(request, user, project_slug):
    project = Project.objects.filter(
        Q(owner=request.user) | Q(authorized=request.user),
        Q(slug=project_slug),
    ).first()

    if request.method == "POST":
        description = request.POST.get("description", "")
        if description != "":
            project.description = description
            project.save()

            log = ProjectLog(
                project=project,
                module="PR",
                headline="Project description",
                description="Changed description for project",
            )
            log.save()

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": request.user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def create_environment(request, user, project_slug):
    # TODO: Ensure that user is allowed to create environment in this project.
    if request.method == "POST":
        project = Project.objects.get(slug=project_slug)
        name = request.POST.get("environment_name")
        repo = request.POST.get("environment_repository")
        image = request.POST.get("environment_image")
        app_pk = request.POST.get("environment_app")
        app = Apps.objects.get(pk=app_pk)
        environment = Environment(
            name=name,
            slug=name,
            project=project,
            repository=repo,
            image=image,
            app=app,
        )
        environment.save()
    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def delete_environment(request, user, project_slug):
    if request.method == "POST":
        project = Project.objects.get(slug=project_slug)
        pk = request.POST.get("environment_pk")
        # TODO: Check that the user has permission to delete this environment.
        environment = Environment.objects.get(pk=pk, project=project)
        environment.delete()

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def create_flavor(request, user, project_slug):
    # TODO: Ensure that user is allowed to create flavor in this project.
    if request.method == "POST":
        # TODO: Check input
        project = Project.objects.get(slug=project_slug)
        print(request.POST)
        name = request.POST.get("flavor_name")
        cpu_req = request.POST.get("cpu_req")
        mem_req = request.POST.get("mem_req")
        gpu_req = request.POST.get("gpu_req")
        cpu_lim = request.POST.get("cpu_lim")
        mem_lim = request.POST.get("mem_lim")
        flavor = Flavor(
            name=name,
            project=project,
            cpu_req=cpu_req,
            mem_req=mem_req,
            gpu_req=gpu_req,
            cpu_lim=cpu_lim,
            mem_lim=mem_lim,
        )
        flavor.save()
    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def delete_flavor(request, user, project_slug):
    if request.method == "POST":
        project = Project.objects.get(slug=project_slug)
        pk = request.POST.get("flavor_pk")
        # TODO: Check that the user has permission to delete this flavor.
        flavor = Flavor.objects.get(pk=pk, project=project)
        flavor.delete()

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def set_s3storage(request, user, project_slug, s3storage=[]):
    # TODO: Ensure that the user has the correct permissions to set
    # this specific
    # s3 object to storage in this project (need to check that
    # the user has access to the
    # project as well.)
    if request.method == "POST" or s3storage:
        project = Project.objects.get(slug=project_slug)

        if s3storage:
            s3obj = S3.objects.get(name=s3storage, project=project)
        else:
            pk = request.POST.get("s3storage")
            if pk == "blank":
                s3obj = None
            else:
                s3obj = S3.objects.get(pk=pk)

        project.s3storage = s3obj
        project.save()

        if s3storage:
            return JsonResponse({"status": "ok"})

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def set_mlflow(request, user, project_slug, mlflow=[]):
    # TODO: Ensure that the user has the correct permissions
    # to set this specific
    # MLFlow object to MLFlow Server in this project (need to check
    #  that the user has access to the
    # project as well.)
    if request.method == "POST" or mlflow:
        project = Project.objects.get(slug=project_slug)

        if mlflow:
            mlflowobj = MLFlow.objects.get(name=mlflow, project=project)
        else:
            pk = request.POST.get("mlflow")
            mlflowobj = MLFlow.objects.get(pk=pk)

        project.mlflow = mlflowobj
        project.save()

        if mlflow:
            return JsonResponse({"status": "ok"})

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project_slug")
    ),
    name="dispatch",
)
class ProjectStatusView(View):
    def get(self, request, user, project_slug):
        project = Project.objects.get(slug=project_slug)

        return JsonResponse({"status": project.status})


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project_slug")
    ),
    name="dispatch",
)
class GrantAccessToProjectView(View):
    def post(self, request, user, project_slug):
        selected_username = request.POST["selected_user"]
        qs = User.objects.filter(username=selected_username)

        if len(qs) == 1:
            selected_user = qs[0]
            project = Project.objects.get(slug=project_slug)

            project.authorized.add(selected_user)
            assign_perm("can_view_project", selected_user, project)

            log = ProjectLog(
                project=project,
                module="PR",
                headline="New members",
                description="1 new members have been added to the Project",
            )

            log.save()

        return HttpResponseRedirect(
            f"/{user}/{project_slug}/settings?template=access"
        )


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project_slug")
    ),
    name="dispatch",
)
class RevokeAccessToProjectView(View):
    def valid_request(self, selected_username, user, project):
        if project.owner.id != user.id:
            return [False, None]

        qs = User.objects.filter(username=selected_username)

        if len(qs) != 1:
            return [False, None]

        selected_user = qs[0]

        if selected_user not in project.authorized.all():
            return [False, None]

        return [True, selected_user]

    def post(self, request, user, project_slug):
        selected_username = request.POST["selected_user"]
        project = Project.objects.get(slug=project_slug)

        valid_request, selected_user = self.valid_request(
            selected_username,
            request.user,
            project,
        )

        if not valid_request:
            return HttpResponseBadRequest()

        project.authorized.remove(selected_user)
        remove_perm("can_view_project", selected_user, project)

        log = ProjectLog(
            project=project,
            module="PR",
            headline="Removed Project members",
            description="1 of members have been removed from the Project",
        )

        log.save()

        return HttpResponseRedirect(
            reverse(
                "projects:settings",
                kwargs={"user": user, "project_slug": project_slug},
            )
        )


@login_required
def project_templates(request):
    template = "project_templates.html"
    templates = (
        ProjectTemplate.objects.filter(enabled=True)
        .order_by("slug", "-revision")
        .distinct("slug")
    )
    media_url = django_settings.MEDIA_URL
    return render(request, template, locals())


class CreateProjectView(View):
    template_name = "project_create.html"

    def get(self, request):
        pre_selected_template = request.GET.get("template")

        arr = ProjectTemplate.objects.filter(name=pre_selected_template)

        template = arr[0] if len(arr) > 0 else None

        context = {"template": template}

        return render(
            request=request,
            context=context,
            template_name=self.template_name,
        )

    def post(self, request, *args, **kwargs):
        success = True

        template_id = request.POST.get("template_id")
        name = request.POST.get("name", "default")
        description = request.POST.get("description", "")

        # Try to create database project object.
        try:
            project = Project.objects.create_project(
                name=name,
                owner=request.user,
                description=description,
                repository="",
                status="created",
            )
        except ProjectCreationException:
            print("ERROR: Failed to create project database object.")
            success = False

        try:
            # Create resources from the chosen template
            project_template = ProjectTemplate.objects.get(pk=template_id)
            create_resources_from_template.delay(
                request.user.username, project.slug, project_template.template
            )

        except ProjectCreationException:
            print("ERROR: could not create project resources")
            success = False

        if not success:
            project.delete()
        else:
            l1 = ProjectLog(
                project=project,
                module="PR",
                headline="Project created",
                description="Created project {}".format(project.name),
            )
            l1.save()

            l2 = ProjectLog(
                project=project,
                module="PR",
                headline="Getting started",
                description="Getting started with project {}".format(project.name),
            )
            l2.save()

        next_page = request.POST.get("next", "/{}/{}".format(request.user, project.slug))

        return HttpResponseRedirect(next_page, {"message": "Created project"})


@method_decorator(
    permission_required_or_403(
        "can_view_project", (Project, "slug", "project_slug")
    ),
    name="dispatch",
)
class DetailsView(View):
    template_name = "projects/overview.html"

    def get(self, request, user, project_slug):
        resources = list()
        models = Model.objects.none()
        app_ids = []
        project = None

        if request.user.is_authenticated:
            project = Project.objects.get(slug=project_slug)
            categories = AppCategories.objects.all().order_by("-priority")
            models = Model.objects.filter(project=project).order_by(
                "-uploaded_at"
            )[:10]

            def filter_func(slug):
                return Q(app__category__slug=slug)

            for category in categories:
                app_instances_of_category = (
                    AppInstance.objects.get_app_instances_of_project(
                        user=request.user,
                        project=project,
                        filter_func=filter_func(slug=category.slug),
                        limit=5,
                    )
                )

                app_ids += [obj.id for obj in app_instances_of_category]

                apps_of_category = (
                    Apps.objects.filter(
                        category=category, user_can_create=True
                    )
                    .order_by("slug", "-revision")
                    .distinct("slug")
                )

                resources.append(
                    {
                        "title": category.name,
                        "objs": app_instances_of_category,
                        "apps": apps_of_category,
                    }
                )

        context = {
            "resources": resources,
            "models": models,
            "project": project,
            "app_ids": app_ids,
        }

        return render(
            request=request,
            context=context,
            template_name=self.template_name,
        )


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def delete(request, user, project_slug):
    next_page = request.GET.get("next", "/projects/")

    if not request.user.is_superuser:
        users = User.objects.filter(username=user)

        if len(users) != 1:
            return HttpResponseBadRequest()

        owner = users[0]

        projects = Project.objects.filter(owner=owner, slug=project_slug)

        if len(projects) != 1:
            return HttpResponseForbidden()

        project = projects[0]
    else:
        project = Project.objects.filter(slug=project_slug).first()

    print("SCHEDULING DELETION OF ALL INSTALLED APPS")
    project.status = "deleted"
    project.save()
    delete_project.delay(project.pk)

    return HttpResponseRedirect(next_page, {"message": "Deleted project successfully."})


@login_required
@permission_required_or_403("can_view_project", (Project, "slug", "project_slug"))
def publish_project(request, user, project_slug):
    owner = User.objects.filter(username=user).first()
    project = Project.objects.filter(owner=owner, slug=project_slug).first()

    if request.method == "POST":
        gh_form = PublishProjectToGitHub(request.POST)

        if gh_form.is_valid():
            user_name = gh_form.cleaned_data["user_name"]
            user_password = gh_form.cleaned_data["user_password"]

            user_password_bytes = user_password.encode("ascii")
            base64_bytes = base64.b64encode(user_password_bytes)
            user_password_encoded = base64_bytes.decode("ascii")

            url = "http://{}-file-controller/project/{}/push/{}/{}".format(
                project_slug,
                project_slug[:-4],
                user_name,
                user_password_encoded,
            )
            try:
                response = r.get(url)

                if response.status_code == 200 or response.status_code == 203:
                    payload = response.json()

                    if payload["status"] == "OK":
                        clone_url = payload["clone_url"]
                        if clone_url:
                            project.clone_url = clone_url
                            project.save()

                            log = ProjectLog(
                                project=project,
                                module="PR",
                                headline="GitHub repository",
                                description=("Published project files" " to a GitHub repository {url}").format(
                                    url=project.clone_url
                                ),
                            )
                            log.save()
            except Exception as e:
                logger.error("Failed to get response from {} with error: {}".format(url, e))

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project_slug},
        )
    )
