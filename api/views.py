import json
import time

from apps.models import AppCategories, AppInstance, Apps
from apps.tasks import delete_resource
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.utils.text import slugify
from django_filters.rest_framework import DjangoFilterBackend
from models.models import ObjectType
from portal.models import PublishedModel
from projects.models import (
    S3,
    Environment,
    Flavor,
    MLFlow,
    ProjectLog,
    ProjectTemplate,
    ReleaseName,
)
from projects.tasks import create_resources_from_template, delete_project_apps
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .APIpermissions import AdminPermission, ProjectPermission
from .serializers import (
    AppInstanceSerializer,
    AppSerializer,
    EnvironmentSerializer,
    FlavorsSerializer,
    Metadata,
    MetadataSerializer,
    MLflowSerializer,
    MLModelSerializer,
    Model,
    ModelLog,
    ModelLogSerializer,
    ObjectTypeSerializer,
    Project,
    ProjectSerializer,
    ProjectTemplateSerializer,
    ReleaseNameSerializer,
    S3serializer,
    UserSerializer,
)


# A customized version of the obtain_auth_token view
# It will either create or fetch the user token
# https://www.django-rest-framework.org/api-guide/authentication/#tokenauthentication
class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {"token": token.key, "user_id": user.pk, "email": user.email}
        )


class ObjectTypeList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = ObjectTypeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "slug"]

    def get_queryset(self):
        return ObjectType.objects.all()


class ModelList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "version", "object_type"]

    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        return Model.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        model = self.get_object()
        if model.project == project:
            model.delete()
            return HttpResponse("ok", 200)
        else:
            return HttpResponse("User is not allowed to delete object.", 403)

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        print(project)

        try:
            model_name = request.data["name"]
            prev_model = Model.objects.filter(
                name=model_name, project=project
            ).order_by("-version")
            print("INFO - Previous Model Objects: {}".format(prev_model))
            if len(prev_model) > 0:
                print("ACCESS")
                access = prev_model[0].access
                print(access)

            else:
                access = "PR"
            release_type = request.data["release_type"]
            version = request.data["version"]
            description = request.data["description"]
            model_card = request.data["model_card"]
            model_uid = request.data["uid"]
            object_type_slug = request.data["object_type"]
            object_type = ObjectType.objects.get(slug=object_type_slug)
        except Exception as err:
            print(err)
            return HttpResponse(
                "Failed to create object: incorrect input data.", 400
            )

        try:
            new_model = Model(
                uid=model_uid,
                name=model_name,
                description=description,
                release_type=release_type,
                version=version,
                model_card=model_card,
                project=project,
                s3=project.s3storage,
                access=access,
            )
            new_model.save()
            new_model.object_type.set([object_type])

            pmodel = PublishedModel.objects.get(
                name=new_model.name, project=new_model.project
            )
            if pmodel:
                # Model is published, so we should create a new
                # PublishModelObject.

                from models.helpers import add_pmo_to_publish

                add_pmo_to_publish(new_model, pmodel)

        except Exception as err:
            print(err)
            return HttpResponse(
                "Failed to create object: failed to save object.", 400
            )
        return HttpResponse("ok", 200)


class ModelLogList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = ModelLogSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['id','name', 'version']

    # Not sure if this kind of function is needed for ModelLog?
    def get_queryset(self):

        return ModelLog.objects.filter(project__pk=self.kwargs["project_pk"])

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])

        try:
            run_id = request.data["run_id"]
            trained_model = request.data["trained_model"]
            training_started_at = request.data["training_started_at"]
            execution_time = request.data["execution_time"]
            code_version = request.data["code_version"]
            current_git_repo = request.data["current_git_repo"]
            latest_git_commit = request.data["latest_git_commit"]
            system_details = request.data["system_details"]
            cpu_details = request.data["cpu_details"]
            training_status = request.data["training_status"]
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("Failed to create training session log.", 400)

        new_log = ModelLog(
            run_id=run_id,
            trained_model=trained_model,
            project=project.name,
            training_started_at=training_started_at,
            execution_time=execution_time,
            code_version=code_version,
            current_git_repo=current_git_repo,
            latest_git_commit=latest_git_commit,
            system_details=system_details,
            cpu_details=cpu_details,
            training_status=training_status,
        )
        new_log.save()
        return HttpResponse("ok", 200)


class MetadataList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = MetadataSerializer
    filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['id','name', 'version']

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])

        try:
            run_id = request.data["run_id"]
            trained_model = request.data["trained_model"]
            model_details = request.data["model_details"]
            parameters = request.data["parameters"]
            metrics = request.data["metrics"]
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("Failed to create metadata log.", 400)

        new_md = Metadata(
            run_id=run_id,
            trained_model=trained_model,
            project=project.name,
            model_details=model_details,
            parameters=parameters,
            metrics=metrics,
        )
        new_md.save()
        return HttpResponse("ok", 200)


class MembersList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        """
        This view should return a list of all the members
        of the project
        """
        proj = Project.objects.filter(pk=self.kwargs["project_pk"])
        owner = proj[0].owner
        auth_users = proj[0].authorized.all()
        print(owner)
        print(auth_users)
        ids = set()
        ids.add(owner.pk)
        for user in auth_users:
            ids.add(user.pk)
        # return [owner, authorized]
        print(ids)
        users = User.objects.filter(pk__in=ids)
        print(users)
        return users

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        selected_users = request.data["selected_users"]
        for username in selected_users.split(","):
            user = User.objects.get(username=username)
            project.authorized.add(user)
        project.save()
        return HttpResponse("Successfully added members.", status=200)

    def destroy(self, request, *args, **kwargs):
        print("removing user")
        project = Project.objects.get(id=self.kwargs["project_pk"])
        user_id = self.kwargs["pk"]
        print(user_id)
        user = User.objects.get(pk=user_id)
        print("user")
        print(user)
        if user.username != project.owner.username:
            print("username" + user.username)
            project.authorized.remove(user)
            for role in settings.PROJECT_ROLES:
                return HttpResponse(
                    "Successfully removed members.", status=200
                )
        else:
            return HttpResponse("Cannot remove owner of project.", status=400)
        return HttpResponse("Failed to remove user.", status=400)


class ProjectList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["name", "slug"]

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Project.objects.filter(
            Q(owner__username=current_user)
            | Q(authorized__pk__exact=current_user.pk),
            ~Q(status="archived"),
        ).distinct("name")

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if (
            request.user == project.owner or request.user.is_superuser
        ) and project.status.lower() != "deleted":
            print("Delete project")
            print("SCHEDULING DELETION OF ALL INSTALLED APPS")
            delete_project_apps(project.slug)

            print("ARCHIVING PROJECT Object")
            objects = Model.objects.filter(project=project)
            for obj in objects:
                obj.status = "AR"
                obj.save()
            project.status = "archived"
            project.save()
        else:
            print("User is not allowed to delete project (must be owner).")
            return HttpResponse(
                "User is not allowed to delete project (must be owner).",
                status=403,
            )

        return HttpResponse("ok", status=200)

    def create(self, request):
        name = request.data["name"]
        description = request.data["description"]
        repository = request.data["repository"]
        project = Project.objects.create_project(
            name=name,
            owner=request.user,
            description=description,
            repository=repository,
        )
        success = True

        try:
            # Create resources from the chosen template
            template_slug = request.data["template"]
            template = ProjectTemplate.objects.get(slug=template_slug)
            project_template = ProjectTemplate.objects.get(pk=template.pk)
            create_resources_from_template.delay(
                request.user.username, project.slug, project_template.template
            )

            # Reset user token
            if "oidc_id_token_expiration" in request.session:
                request.session["oidc_id_token_expiration"] = time.time() - 100
                request.session.save()
            else:
                print("No token to reset.")
        except Exception as e:
            print("ERROR: could not create project resources")
            print(e)
            success = False

        if not success:
            project.delete()
            return HttpResponse("Failed to create project.", status=200)
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

        if success:
            project.save()
            return HttpResponse(project.slug, status=200)


class ResourceList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = AppInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "app__category"]

    def create(self, request, *args, **kwargs):
        template = request.data
        # template = {
        #     "apps": request.data
        # }
        print(template)
        project = Project.objects.get(id=self.kwargs["project_pk"])
        create_resources_from_template.delay(
            request.user.username, project.slug, json.dumps(template)
        )
        return HttpResponse("Submitted request to create app.", status=200)


class AppInstanceList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = AppInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "app__category"]

    def get_queryset(self):
        return AppInstance.objects.filter(
            ~Q(state="Deleted"), project__pk=self.kwargs["project_pk"]
        )

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        app_slug = request.data["slug"]
        data = request.data
        user = request.user
        import apps.views as appviews

        request = HttpRequest()
        request.user = user
        _ = appviews.create(
            request,
            user=user.username,
            data=data,
            project=project.slug,
            app_slug=app_slug,
            wait=True,
            call=True,
        )
        return HttpResponse("App created.", status=200)

    def destroy(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        appinstance = self.get_object()
        # Check that user is allowed to delete app:
        # Either user owns the app, or is a member of the project
        # (Checked by project permission above)
        # and the app is set to project level permission.
        access = False
        if appinstance.owner == request.user:
            print("User owns app, can delete.")
            access = True
        elif appinstance.permission.projects.filter(
            slug=project.slug
        ).exists():
            print("Project has permission")
            access = True
        elif appinstance.permission.public:
            print(
                "Public app and user has project permission, delete granted."
            )
            access = True
        if access:
            delete_resource.delay(appinstance.pk)
        else:
            return HttpResponse(
                "User is not allowed to delete resource.", status=403
            )
        return HttpResponse("Deleted app.", status=200)


class FlavorsList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = FlavorsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]

    def get_queryset(self):
        return Flavor.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class EnvironmentList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = EnvironmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]

    def get_queryset(self):
        return Environment.objects.filter(
            project__pk=self.kwargs["project_pk"]
        )

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class S3List(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = S3serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "host", "region"]

    def get_queryset(self):
        return S3.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class MLflowList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = MLflowSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name"]

    def get_queryset(self):
        return MLFlow.objects.filter(project__pk=self.kwargs["project_pk"])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class ReleaseNameList(
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        ProjectPermission,
    )
    serializer_class = ReleaseNameSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "project"]

    def get_queryset(self):
        return ReleaseName.objects.filter(
            project__pk=self.kwargs["project_pk"]
        )

    def create(self, request, *args, **kwargs):
        name = slugify(request.data["name"])
        project = Project.objects.get(id=self.kwargs["project_pk"])
        if ReleaseName.objects.filter(name=name).exists():
            if project.status != "archived":
                print("ReleaseName already in use.")
                return HttpResponse("Release name already in use.", status=200)
        status = "active"

        rn = ReleaseName(name=name, status=status, project=project)
        rn.save()
        return HttpResponse(
            "Created release name {}.".format(name), status=200
        )

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class AppList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        AdminPermission,
    )
    serializer_class = AppSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "slug", "category"]

    def get_queryset(self):
        return Apps.objects.all()

    def create(self, request, *args, **kwargs):
        print("IN CREATE")
        try:
            name = request.data["name"]
            slug = request.data["slug"]
            category = AppCategories.objects.get(slug=request.data["cat"])
            description = request.data["description"]
            settings = json.loads(request.data["settings"])
            table_field = json.loads(request.data["table_field"])
            priority = request.data["priority"]
            access = "public"
            proj_list = []
            if "access" in request.data:
                try:
                    access = request.data["access"]
                    if access != "public":
                        projs = access.split(",")
                        for proj in projs:
                            tmp = Project.objects.get(slug=proj)
                            proj_list.append(tmp)
                except Exception as e:
                    print("Invalid access field")
                    print(e, flush=True)
                    return HttpResponse("Invalid access field.", status=400)

            print(request.data)
            print("SETTINGS")
            print(settings)
            print(table_field)
        except Exception as err:
            print(request.data)
            print(err)
            return HttpResponse("Invalid app specification.", status=400)
        print("ADD APP")
        print(name)
        print(slug)
        try:
            app_latest_rev = Apps.objects.filter(slug=slug).order_by(
                "-revision"
            )
            if app_latest_rev:
                revision = app_latest_rev[0].revision + 1
            else:
                revision = 1
            app = Apps(
                name=name,
                slug=slug,
                category=category,
                settings=settings,
                chart_archive=request.FILES["chart"],
                revision=revision,
                description=description,
                table_field=table_field,
                priority=int(priority),
                access=access,
                logo_file=request.FILES["logo"],
            )
            app.save()
            app.projects.add(*proj_list)
        except Exception as err:
            print(err)
        return HttpResponse("Created new app.", status=200)

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except Exception as e:
            print(e, flush=True)
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)


class ProjectTemplateList(
    generics.ListAPIView,
    GenericViewSet,
    CreateModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
):
    permission_classes = (
        IsAuthenticated,
        AdminPermission,
    )
    serializer_class = ProjectTemplateSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["id", "name", "slug"]

    def get_queryset(self):
        return ProjectTemplate.objects.all()

    def create(self, request, *args, **kwargs):
        print(request.data)
        try:
            settings = json.loads(request.data["settings"])
            name = settings["name"]
            slug = settings["slug"]
            description = settings["description"]
            template = settings["template"]
            image = request.FILES["image"]
        except Exception as err:
            print(request.data)
            print(err)
            return HttpResponse(
                "Failed to create new template: {}".format(name), status=400
            )

        try:
            template_latest_rev = ProjectTemplate.objects.filter(
                slug=slug
            ).order_by("-revision")
            if template_latest_rev:
                revision = template_latest_rev[0].revision + 1
            else:
                revision = 1
            template = ProjectTemplate(
                name=name,
                slug=slug,
                revision=revision,
                description=description,
                template=json.dumps(template),
                image=image,
            )
            template.save()
        except Exception as err:
            print(err)
        return HttpResponse(
            "Created new template: {}.".format(name), status=200
        )
