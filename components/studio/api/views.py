import uuid
import json
from ast import literal_eval
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.utils.text import slugify
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .APIpermissions import ProjectPermission
from deployments.helpers import build_definition
from projects.helpers import create_project_resources
from projects.tasks import create_resources_from_template, delete_project_apps
from django.contrib.auth.models import User
from django.conf import settings
import modules.keycloak_lib as kc
from projects.models import Environment, Flavor, S3, MLFlow, ProjectTemplate, ProjectLog, ReleaseName
from models.models import ObjectType
from apps.models import AppInstance

from .serializers import Model, MLModelSerializer, ModelLog, ModelLogSerializer, Metadata, MetadataSerializer, Project, ProjectSerializer, UserSerializer
from .serializers import ObjectTypeSerializer, AppInstanceSerializer, FlavorsSerializer
from .serializers import EnvironmentSerializer, S3serializer, MLflowSerializer, ReleaseNameSerializer

from projects.tasks import create_resources_from_template
from apps.tasks import delete_resource

class ObjectTypeList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = ObjectTypeSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'slug']

    def get_queryset(self):
        return ObjectType.objects.all()

class ModelList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'version', 'object_type']

    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        return Model.objects.filter(project__pk=self.kwargs['project_pk'])

    def destroy(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs['project_pk'])
        model = self.get_object()
        if model.project==project:
            model.delete()
            return HttpResponse('ok', 200)
        else:
            return HttpResponse('User is not allowed to delete object.', 403)

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs['project_pk'])
        print(project)

        try:
            model_name = request.data['name']
            release_type = request.data['release_type']
            description = request.data['description']
            model_uid = request.data['uid']
            object_type_slug = request.data['object_type']
            object_type = ObjectType.objects.get(slug=object_type_slug)
        except Exception as err:
            print(err)
            return HttpResponse('Failed to create object: incorrect input data.', 400)

        try:
            new_model = Model(name=model_name,
                            release_type=release_type,
                            description=description,
                            uid=model_uid,
                            project=project,
                            s3=project.s3storage)
            new_model.save()
            new_model.object_type.set([object_type])
        except Exception as err:
            print(err)
            return HttpResponse('Failed to create object: failed to save object.', 400)
        return HttpResponse('ok', 200)


class ModelLogList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = ModelLogSerializer
    filter_backends = [DjangoFilterBackend]
    #filterset_fields = ['id','name', 'version']

    # Not sure if this kind of function is needed for ModelLog?
    def get_queryset(self):
        
        return ModelLog.objects.filter(project__pk=self.kwargs['project_pk'])

    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs['project_pk'])
        
        try:
            run_id = request.data['run_id']
            trained_model = request.data['trained_model']
            training_started_at = request.data['training_started_at']
            execution_time = request.data['execution_time']
            code_version = request.data['code_version']
            current_git_repo = request.data['current_git_repo']
            latest_git_commit = request.data['latest_git_commit']
            system_details = request.data['system_details']
            cpu_details = request.data['cpu_details']
            training_status = request.data['training_status']
        except:
            return HttpResponse('Failed to create training session log.', 400)

        new_log = ModelLog(run_id=run_id, trained_model=trained_model, project=project.name, training_started_at=training_started_at, execution_time=execution_time,
                           code_version=code_version, current_git_repo=current_git_repo, latest_git_commit=latest_git_commit, 
                           system_details=system_details, cpu_details=cpu_details, training_status=training_status, )
        new_log.save()
        return HttpResponse('ok', 200)


class MetadataList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = MetadataSerializer
    filter_backends = [DjangoFilterBackend]
    #filterset_fields = ['id','name', 'version']
    
    def create(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs['project_pk'])
        
        try:
            run_id = request.data['run_id']
            trained_model = request.data['trained_model']
            model_details = request.data['model_details']
            parameters = request.data['parameters']
            metrics = request.data['metrics']
        except:
            return HttpResponse('Failed to create metadata log.', 400)

        new_md = Metadata(run_id=run_id, trained_model=trained_model, project=project.name,  
                          model_details=model_details, parameters=parameters, metrics=metrics, )
        new_md.save()
        return HttpResponse('ok', 200)



class MembersList(generics.ListAPIView, GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin,
                  ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission, )
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend]
    
    def get_queryset(self):
        """
        This view should return a list of all the members
        of the project
        """
        proj = Project.objects.filter(pk=self.kwargs['project_pk'])
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
        project = Project.objects.get(id=self.kwargs['project_pk'])
        selected_users = request.data['selected_users']
        role = request.data['role']
        for username in selected_users.split(','):
            user = User.objects.get(username=username)
            project.authorized.add(user)
            kc.keycloak_add_role_to_user(project.slug, user.username, role)
        project.save()
        return HttpResponse('Successfully added members.', status=200)

    def destroy(self, request, *args, **kwargs):
        print('removing user')
        project = Project.objects.get(id=self.kwargs['project_pk'])
        user_id = self.kwargs['pk']
        print(user_id)
        user = User.objects.get(pk=user_id)
        print('user')
        print(user)
        if user.username != project.owner.username:
            print('username'+user.username)
            project.authorized.remove(user)
            for role in settings.PROJECT_ROLES:
                kc.keycloak_add_role_to_user(project.slug, user.username, role, action='delete')
            return HttpResponse('Successfully removed members.', status=200)
        else:
            return HttpResponse('Cannot remove owner of project.', status=400)
        return HttpResponse('Failed to remove user.', status=400)

class ProjectList(generics.ListAPIView, GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin,
                  ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'slug']

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Project.objects.filter(Q(owner__username=current_user) | Q(authorized__pk__exact=current_user.pk), ~Q(status='archived'))
    
    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if request.user == project.owner and project.status.lower() != "deleted":
            print("Delete project")

            print("Cleaning up Keycloak.")
            keyc = kc.keycloak_init()
            kc.keycloak_delete_client(keyc, project.slug)
            
            scope_id, res = kc.keycloak_get_client_scope_id(keyc, project.slug+'-scope')
            print(scope_id)
            kc.keycloak_delete_client_scope(keyc, scope_id)

            print("KEYCLOAK RESOURCES DELETED SUCCESFULLY!")
            print("SCHEDULING DELETION OF ALL INSTALLED APPS")
            delete_project_apps(project.slug)

            print("ARCHIVING PROJECT Object")
            objects = Model.objects.filter(project=project)
            for obj in objects:
                obj.status = 'AR'
                obj.save()
            project.status = 'archived'
            project.save()
        else:
            print("User is not allowed to delete project (only owner can delete).")
            return HttpResponse("User is not allowed to delete project (only owner can delete).", status=403)

        return HttpResponse('ok', status=200)

    def create(self, request):
        name = request.data['name']
        description = request.data['description']
        repository = request.data['repository']
        project = Project.objects.create_project(name=name,
                                                 owner=request.user,
                                                 description=description,
                                                 repository=repository)
        success = True
        
        try:
            # Create project resources (Keycloak only)
            create_project_resources(project, request.user.username, repository)

            # Create resources from the chosen template
            template_slug = request.data['template']
            template = ProjectTemplate.objects.get(slug=template_slug)
            project_template = ProjectTemplate.objects.get(pk=template.pk)
            create_resources_from_template.delay(request.user.username, project.slug, project_template.template)

            # Reset user token
            if 'oidc_id_token_expiration' in request.session:
                request.session['oidc_id_token_expiration'] = time.time()-100
                request.session.save()
            else:
                print("No token to reset.")
        except Exception as e:
            print("ERROR: could not create project resources")
            print(e)
            success = False

        if not success:
            project.delete()
            return HttpResponse('Failed to create project.', status=200)
        else:
            l1 = ProjectLog(project=project, module='PR', headline='Project created',
                            description='Created project {}'.format(project.name))
            l1.save()

            l2 = ProjectLog(project=project, module='PR', headline='Getting started',
                            description='Getting started with project {}'.format(project.name))
            l2.save()


        if success:
            project.save()
            return HttpResponse(project.slug, status=200)


class ResourceList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = AppInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'app__category']

    # def get_queryset(self):
    #     return AppInstance.objects.filter(~Q(state="Deleted"), project__pk=self.kwargs['project_pk'])
    
    def create(self, request, *args, **kwargs):
        template = request.data
        # template = {
        #     "apps": request.data
        # }
        print(template)
        project = Project.objects.get(id=self.kwargs['project_pk'])
        create_resources_from_template.delay(request.user.username, project.slug, json.dumps(template))
        return HttpResponse("Submitted request to create app.", status=200)

class AppInstanceList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = AppInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'app__category']

    def get_queryset(self):
        return AppInstance.objects.filter(~Q(state="Deleted"), project__pk=self.kwargs['project_pk'])
    
    def create(self, request, *args, **kwargs):
        return HttpResponse("Use 'resources' endpoint instead.", status=200)

    def destroy(self, request, *args, **kwargs):
        project = Project.objects.get(id=self.kwargs['project_pk'])
        appinstance = self.get_object()
        # Check that user is allowed to delete app:
        # Either user owns the app, or is a member of the project (Checked by project permission above)
        # and the app is set to project level permission.
        access = False
        if appinstance.owner == request.user:
            print("User owns app, can delete.")
            access = True
        elif appinstance.permission.projects.filter(slug=project.slug).exists():
            print("Project has permission")
            access = True
        elif appinstance.permission.public:
            print("App is public and user has project permission, allowed to delete.")
            access = True
        # Q(owner=request.user) | Q(permission__projects__slug=project.slug) |  Q(permission__public=True)
        if access:
            delete_resource.delay(appinstance.pk)
        else:
            return HttpResponse("User is not allowed to delete resource.", status=403)
        return HttpResponse("Deleted app.", status=200)

class FlavorsList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = FlavorsSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name']

    def get_queryset(self):
        return Flavor.objects.filter(project__pk=self.kwargs['project_pk'])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except:
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)

class EnvironmentList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = EnvironmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name']

    def get_queryset(self):
        return Environment.objects.filter(project__pk=self.kwargs['project_pk'])
    
    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except:
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)

class S3List(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = S3serializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'host', 'region']

    def get_queryset(self):
        return S3.objects.filter(project__pk=self.kwargs['project_pk'])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except:
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)

class MLflowList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = MLflowSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name']

    def get_queryset(self):
        return MLFlow.objects.filter(project__pk=self.kwargs['project_pk'])

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except:
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)

class ReleaseNameList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = ReleaseNameSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'project']

    def get_queryset(self):
        return ReleaseName.objects.filter(project__pk=self.kwargs['project_pk'])

    def create(self, request, *args, **kwargs):
        name = slugify(request.data['name'])
        project = Project.objects.get(id=self.kwargs['project_pk'])
        if ReleaseName.objects.filter(name=name).exists():
            if project.status != 'archived':
                print("ReleaseName already in use.")
                return HttpResponse("Release name already in use.", status=200)
        status = 'active'
        
        rn = ReleaseName(name=name, status=status, project=project)
        rn.save()
        return HttpResponse("Created release name {}.".format(name), status=200)

    def destroy(self, request, *args, **kwargs):
        try:
            obj = self.get_object()
        except:
            return HttpResponse("No such object.", status=400)
        obj.delete()
        return HttpResponse("Deleted object.", status=200)