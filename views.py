import base64
import logging
import random

import requests as r
from django.apps import apps
from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist
from django.core.files import File
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, reverse
from guardian.decorators import permission_required_or_403
from guardian.shortcuts import assign_perm, remove_perm

from .exceptions import ProjectCreationException
from .forms import (
    ImageUpdateForm,
    PublishProjectToGitHub,
    TransferProjectOwnershipForm,
)
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


def index(request):
    template = "projects/index.html"
    try:
        if request.user.is_superuser:
            projects = Project.objects.filter(status="active").distinct("pk")
        else:
            projects = Project.objects.filter(
                Q(owner=request.user) | Q(authorized=request.user),
                status="active",
            ).distinct("pk")
        media_url = django_settings.MEDIA_URL
        print(django_settings.STATIC_ROOT)
    except TypeError as err:
        projects = []
        print(err)

    request.session["next"] = "/projects/"
    return render(request, template, locals())


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def settings(request, user, project_slug):
    try:
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(authorized=request.user), status="active"
        ).distinct("pk")
    except TypeError as err:
        projects = []
        print(err)

    template = "projects/settings.html"
    project = Project.objects.filter(
        Q(owner=request.user) | Q(authorized=request.user),
        Q(slug=project_slug),
    ).first()
    url_domain = django_settings.DOMAIN
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

    s3instances = S3.objects.filter(
        Q(project=project), Q(app__state="Running")
    )
    flavors = Flavor.objects.filter(project=project)
    mlflows = MLFlow.objects.filter(
        Q(project=project), Q(app__state="Running")
    )

    registry_app = Apps.objects.get(slug="docker-registry")
    registries = AppInstance.objects.filter(
        app=registry_app.pk, project=project
    )

    return render(request, template, locals())


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def transfer_owner(request, user, project_slug):
    project = Project.objects.get(slug=project_slug)
    if request.method == "POST":
        form = TransferProjectOwnershipForm(request.POST)
        if form.is_valid():
            new_owner_id = int(form.cleaned_data["transfer_to"])
            new_owner = User.objects.filter(pk=new_owner_id).first()
            project.authorized.add(project.owner)
            project.owner = new_owner
            if not new_owner.has_perm("can_view_project", project):
                assign_perm("can_view_project", new_owner, project)
            project.save()

            log = ProjectLog(
                project=project,
                module="PR",
                headline="Project owner",
                description="Transferred Project ownership to {owner}".format(
                    owner=project.owner.username
                ),
            )
            log.save()

            return HttpResponseRedirect("/projects/")
    else:
        form = TransferProjectOwnershipForm()


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def update_image(request, user, project_slug):
    project = Project.objects.filter(
        Q(owner=request.user) | Q(authorized=request.user),
        Q(slug=project_slug),
    ).first()

    if request.method == "POST" and request.FILES["image"]:
        form = ImageUpdateForm(request.POST, request.FILES)

        if form.is_valid():
            image = request.FILES["image"]

            project.project_image = image
            project.save()

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": request.user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def grant_access_to_project(request, user, project_slug):
    project = Project.objects.get(slug=project_slug)

    if request.method == "POST":
        selected_users = request.POST.getlist("selected_users")

        log = ProjectLog(
            project=project,
            module="PR",
            headline="New members",
            description=(
                "{number} new members have been added to the Project"
            ).format(number=len(selected_users)),
        )
        log.save()

        if len(selected_users) == 1:
            selected_users = list(selected_users)

        for _user in selected_users:
            user_tmp = User.objects.get(pk=_user)
            project.authorized.add(user_tmp)
            assign_perm("can_view_project", user_tmp, project)
            username_tmp = user_tmp.username
            logger.info(
                "Trying to add user {} to project.".format(username_tmp)
            )

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def revoke_access_to_project(request, user, project_slug):
    project = Project.objects.get(slug=project_slug)

    if request.method == "POST":
        selected_users = request.POST.getlist("selected_users")

        log = ProjectLog(
            project=project,
            module="PR",
            headline="Removed Project members",
            description=(
                "{number} of members have been removed from the Project"
            ).format(number=len(selected_users)),
        )
        log.save()

        if len(selected_users) == 1:
            selected_users = list(selected_users)

        for selected_user in selected_users:
            user_tmp = User.objects.get(pk=selected_user)
            project.authorized.remove(user_tmp)
            remove_perm("can_view_project", user_tmp, project)
            username_tmp = user_tmp.username
            logger.info(
                "Trying to remove user access {} to project.".format(
                    username_tmp
                )
            )

    # TODO: Currently all project members with 'can_view_projects'
    # can revoke access
    # this handles when the user "remove" herself from the project
    _user = User.objects.get(username=user)
    if str(_user.pk) in selected_users:
        return HttpResponseRedirect("/")

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project.slug},
        )
    )


@login_required
def project_templates(request):
    template = "project_templates.html"
    templates = (
        ProjectTemplate.objects.all()
        .order_by("slug", "-revision")
        .distinct("slug")
    )
    media_url = django_settings.MEDIA_URL
    return render(request, template, locals())


@login_required
def create(request):
    template = "project_create.html"
    templates = (
        ProjectTemplate.objects.all()
        .order_by("slug", "-revision")
        .distinct("slug")
    )

    template_selected = "STACKn Default"
    if "template" in request.GET:
        template_selected = request.GET.get("template")

    if request.method == "POST":
        success = True

        name = request.POST.get("name", "default")
        access = request.POST.get("access", "org")
        description = request.POST.get("description", "")
        repository = request.POST.get("repository", "")

        # Try to create database project object.
        try:
            if django_settings.STATICFILES_DIRS:
                (static_files,) = django_settings.STATICFILES_DIRS
            else:
                static_files = django_settings.STATIC_ROOT
            print(f"STATIC FILES DIR: {static_files}", flush=True)
            img = static_files + "/images/patterns/image-{}.png".format(
                random.randrange(8, 13)
            )
            print(img)
            img_file = open(img, "rb")
            project = Project.objects.create_project(
                name=name,
                owner=request.user,
                description=description,
                repository=repository,
            )
            project.project_image.save("default.png", File(img_file))
            img_file.close()
        except ProjectCreationException:
            print("ERROR: Failed to create project database object.")
            success = False

        try:
            # Create resources from the chosen template
            project_template = ProjectTemplate.objects.get(
                pk=request.POST.get("project-template")
            )
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
                description="Getting started with project {}".format(
                    project.name
                ),
            )
            l2.save()

        next_page = request.POST.get(
            "next", "/{}/{}".format(request.user, project.slug)
        )

        return HttpResponseRedirect(next_page, {"message": "Created project"})

    return render(request, template, locals())


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def details(request, user, project_slug):
    is_authorized = False
    try:
        projects = Project.objects.filter(
            Q(owner=request.user) | Q(authorized=request.user), status="active"
        ).distinct("pk")
    except TypeError as err:
        projects = []
        print(err)
    if request.user.is_superuser:
        is_authorized = True
    else:
        if request.user.is_authenticated:
            is_authorized = True
            request.session["project"] = project_slug

    template = "projects/overview.html"

    url_domain = django_settings.DOMAIN
    media_url = django_settings.MEDIA_URL

    project = None
    message = None
    # username = request.user.username
    try:
        # owner = User.objects.filter(username=username).first()
        project = Project.objects.get(slug=project_slug)
        if is_authorized:
            request.session["project_name"] = project.name
    except Exception:
        message = "Project not found."

    if project:
        pk_list = ""

        status_success = django_settings.APPS_STATUS_SUCCESS
        status_warning = django_settings.APPS_STATUS_WARNING
        activity_logs = ProjectLog.objects.filter(project=project).order_by(
            "-created_at"
        )[:5]
        resources = list()
        cats = AppCategories.objects.all().order_by("-priority")
        rslugs = []
        for cat in cats:
            rslugs.append({"slug": cat.slug, "name": cat.name})

        for rslug in rslugs:
            tmp = AppInstance.objects.filter(
                ~Q(state="Deleted"),
                Q(owner=request.user)
                | Q(permission__projects__slug=project.slug)
                | Q(permission__public=True),
                project=project,
                app__category__slug=rslug["slug"],
            ).order_by("-created_on")[:5]
            for instance in tmp:
                pk_list += str(instance.pk) + ","
            apps_filtered = (
                Apps.objects.filter(
                    category__slug=rslug["slug"], user_can_create=True
                )
                .order_by("slug", "-revision")
                .distinct("slug")
            )
            resources.append(
                {"title": rslug["name"], "objs": tmp, "apps": apps_filtered}
            )
        pk_list = pk_list[:-1]
        pk_list = "'" + pk_list + "'"
        models = Model.objects.filter(project=project).order_by(
            "-uploaded_at"
        )[:10]

    return render(request, template, locals())


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
def delete(request, user, project_slug):
    next_page = request.GET.get("next", "/projects/")

    if not request.user.is_superuser:
        owner = User.objects.filter(username=user).first()
        project = Project.objects.filter(
            owner=owner, slug=project_slug
        ).first()
    else:
        project = Project.objects.filter(slug=project_slug).first()

    print("SCHEDULING DELETION OF ALL INSTALLED APPS")
    project.status = "deleted"
    project.save()
    delete_project.delay(project.pk)

    return HttpResponseRedirect(
        next_page, {"message": "Deleted project successfully."}
    )


@login_required
@permission_required_or_403(
    "can_view_project", (Project, "slug", "project_slug")
)
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
                                description=(
                                    "Published project files"
                                    " to a GitHub repository {url}"
                                ).format(url=project.clone_url),
                            )
                            log.save()
            except Exception as e:
                logger.error(
                    "Failed to get response from {} with error: {}".format(
                        url, e
                    )
                )

    return HttpResponseRedirect(
        reverse(
            "projects:settings",
            kwargs={"user": user, "project_slug": project_slug},
        )
    )
