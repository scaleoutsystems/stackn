import requests
import json
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from deployments.helpers import build_definition


from .serializers import Model, MLModelSerializer, Report, ReportSerializer, \
    ReportGenerator, ReportGeneratorSerializer, Project, ProjectSerializer, \
    DeploymentInstance, DeploymentInstanceSerializer, DeploymentDefinition, \
    DeploymentDefinitionSerializer

class ModelList(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = MLModelSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['id','name', 'tag']

    def get_queryset(self):
        """
        This view should return a list of all the models
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Model.objects.filter(project__owner__username=current_user)
    
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
    filterset_fields = ['id', 'model']
    def get_queryset(self):
        """
        This view should return a list of all the deployments
        for the currently authenticated user.
        """
        current_user = self.request.user
        return DeploymentInstance.objects.filter(model__project__owner__username=current_user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        current_user = self.request.user
        if current_user == instance.model.project.owner:
            instance.delete()
            return HttpResponse('ok', 200)
        else:
            return HttpResponse('Not Allowed', 400)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def build_instance(self, request):

        model_name = request.data['name']
        model_tag = request.data['tag']
        environment = request.data['depdef']    

        try:
            # TODO: Check that we have permission to access the model.
            mod = Model.objects.get(name=model_name, tag=model_tag)
            if mod.status == 'DP':
                return HttpResponse('Model {}:{} already deployed.'.format(model_name, model_tag), status=400)
        except:
            return HttpResponse('Model {}:{} not found.'.format(model_name, model_tag), status=400)
        
        try:
            # TODO: Check that we have permission to access the deployment definition.
            dep = DeploymentDefinition.objects.get(name=environment)
        except:
            return HttpResponse('Deployment environment {} not found.'.format(environment), status=404)

        instance = DeploymentInstance(model=mod, deployment=dep)
        instance.save()
        
        return HttpResponse('ok', status=200)

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
    filterset_fields = ['name']

    def get_queryset(self):
        """
        This view should return a list of all the projects
        for the currently authenticated user.
        """
        current_user = self.request.user
        return Project.objects.filter(owner__username=current_user)
