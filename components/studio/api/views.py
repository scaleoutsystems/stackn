import requests
import json
from ast import literal_eval
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from deployments.helpers import build_definition
from projects.helpers import create_project_resources

from .serializers import Model, MLModelSerializer, Report, ReportSerializer, \
    ReportGenerator, ReportGeneratorSerializer, Project, ProjectSerializer, \
    DeploymentInstance, DeploymentInstanceSerializer, DeploymentDefinition, \
    DeploymentDefinitionSerializer

class ModelList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'version', 'project']

    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Model.objects.filter(project__owner__username=current_user)


    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def release(self, request):
        # Could we get the token here for authorization?
        # We should check that the authenticated user also has
        # the correct role in Keycloak.
        project = Project.objects.get(id=request.data['project'])
        current_user = self.request.user
        if current_user == project.owner:
            # project = model.project
            model_name = request.data['name']
            release_type = request.data['release_type']
            description = request.data['description']
            model_uid = request.data['uid']
            # project_id = request.data['project']
            new_model = Model(name=model_name,
                              release_type=release_type,
                              description=description,
                              uid=model_uid,
                              project=project)
            new_model.save()
            return HttpResponse('ok', 200)


    def destroy(self, request, *args, **kwargs):
        model = self.get_object()
        current_user = self.request.user
        if current_user == model.project.owner:
            model.delete()
            return HttpResponse('ok', 200)
        else:
            return HttpResponse('Not Allowed', 400)

class DeploymentDefinitionList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeploymentDefinitionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def build_definition(self, request):
        instance = DeploymentDefinition.objects.get(name=request.data['name'])
        build_definition(instance)
        return HttpResponse('ok', 200)


    def get_queryset(self):
        """
        This view should return a list of all the deployments
        for the currently authenticated user.
        """
        current_user = self.request.user
        return DeploymentDefinition.objects.filter(project__owner__username=current_user)


class DeploymentInstanceList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeploymentInstanceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id']
    def get_queryset(self):
        """
        This view should return a list of all the deployments
        for the currently authenticated user.
        """
        current_user = self.request.user
        print(self.request.query_params)
        project = self.request.query_params.get('project', [])
        model = self.request.query_params.get('model', [])
        if model:
            return DeploymentInstance.objects.filter(model__project__owner__username=current_user, model__project=project, model=model)
        else:
            return DeploymentInstance.objects.filter(model__project__owner__username=current_user, model__project=project)
    
    def destroy(self, request, *args, **kwargs):
        current_user = self.request.user
        name = self.request.query_params.get('name', [])
        version = self.request.query_params.get('version', [])
        if name and version:
            instance = DeploymentInstance.objects.get(model__name=name, model__version=version)
            print('Deleting deployment of model {}-{}.'.format(name, version))
        else:
            return HttpResponse('Takes model and tag as parameters.', 400)
        if current_user == instance.model.project.owner:
            resource = instance.helmchart
            resource.delete()
            return HttpResponse('ok', 200)
        else:
            return HttpResponse('Not Allowed', 400)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def build_instance(self, request):

        model_name = request.data['name']
        model_version = request.data['version']
        environment = request.data['depdef']
        project_id = request.data['project']
        project = Project.objects.get(pk=project_id)
        print(model_name+':'+model_version)
        try:
            print('Check model')
            # TODO: Check that we have permission to access the model.
            if model_version=='latest':
                mod = Model.objects_version.latest(model_name, project)
            else:
                mod = Model.objects.get(name=model_name, version=model_version, project=project)
            if mod.status == 'DP':
                return HttpResponse('Model {}:{} already deployed.'.format(model_name, model_version), status=400)
        except:
            return HttpResponse('Model {}:{} not found.'.format(model_name, model_version), status=400)
        
        try:
            # TODO: Check that we have permission to access the deployment definition.
            dep = DeploymentDefinition.objects.get(name=environment)
        except:
            return HttpResponse('Deployment environment {} not found.'.format(environment), status=404)

        instance = DeploymentInstance(model=mod, deployment=dep, created_by=request.user)
        instance.save()
        
        return HttpResponse('ok', status=200)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def update_instance(self, request):
        # This implementation is a proof-of-concept, and is used to test
        # the chart controller upgrade functionality
        current_user = request.user
        name = request.data['name']
        version = request.data['version']
        # Currently only allows updating of the number of replicas.
        # This code can be improved and generalized later on. We cannot
        # allow general helm upgrades though, as this can cause STACKn-wide
        # problems.
        try:
            replicas = int(self.request.data['replicas'])
        except:
            return HttpResponse('Replicas parameter should be an integer.', 400)
        print(replicas)
        if replicas < 0 or (isinstance(replicas, int) == False):
            return HttpResponse('Replicas parameter should be positive integer.', 400)

        if name and version:
            instance = DeploymentInstance.objects.get(model__name=name, model__version=version)
            print('instance name: '+instance.model.name)
        else:
            return HttpResponse('Requires model name and version as parameters.', 400)
        # Who should be allowed to update the model? Currently only the owner.
        if current_user == instance.model.project.owner:
            params = instance.helmchart.params
            params = literal_eval(params)
            params['replicas'] = str(replicas)
            print(params)
            instance.helmchart.params = params
            instance.helmchart.save()
            return HttpResponse('Ok', status=200)

        
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def auth(self, request):
      auth_req_red = request.headers['X-Auth-Request-Redirect'].replace('predict/','')
      subs = auth_req_red.split('/')
      release = '{}-{}-{}'.format(subs[1], subs[3], subs[4])
      try:
          instance = DeploymentInstance.objects.get(release=release)
      except:
          return HttpResponse(status=500)
      if instance.access == 'PU' or instance.model.project.owner == request.user:
          return HttpResponse('Ok', status=200)
      else:
          return HttpResponse(status=401)

class ReportList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportSerializer

    def get_queryset(self):
        """
        This view should return a list of all the reports
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Report.objects.filter(generator__project__owner__username=current_user)


class ReportGeneratorList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReportGeneratorSerializer

    def get_queryset(self):
        """
        This view should return a list of all the report generators
        for the currently authenticated user.
        """
        current_user = self.request.user
        return ReportGenerator.objects.filter(project__owner__username=current_user)


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
        return Project.objects.filter(owner__username=current_user)
    
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
