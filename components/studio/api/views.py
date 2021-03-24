import uuid
from ast import literal_eval
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Q
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .APIpermissions import ProjectPermission
from deployments.helpers import build_definition
from projects.helpers import create_project_resources
from django.contrib.auth.models import User
from django.conf import settings
import modules.keycloak_lib as kc
from projects.models import Environment
from models.models import ObjectType

from .serializers import Model, MLModelSerializer, ModelLog, ModelLogSerializer, Metadata, MetadataSerializer, Project, ProjectSerializer, UserSerializer

class ModelList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated, ProjectPermission,)
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'version']

    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        return Model.objects.filter(project__pk=self.kwargs['project_pk'])

    def destroy(self, request, *args, **kwargs):
        model = self.get_object()
        model.delete()
        return HttpResponse('ok', 200)

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
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def create_project(self, request):
        name = request.data['name']
        description = request.data['description']
        repository = request.data['repository']
        project = Project.objects.create_project(name=name,
                                                 owner=request.user,
                                                 description=description,
                                                 repository=repository)
        success = True
        try:
            create_project_resources(project, request.user, repository=repository)
        except:
            print("ERROR: could not create project resources")
            success = False
            return HttpResponse('Ok', status=400)

        if success:
            project.save()
            return HttpResponse('Ok', status=200)
