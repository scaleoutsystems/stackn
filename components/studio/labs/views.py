from django.shortcuts import render, HttpResponseRedirect, reverse
from projects.models import Project, ProjectLog
from .models import Session
from projects.models import Environment, Flavor
from clusters.models import Cluster
from django.contrib.auth.decorators import login_required
import uuid
from django.conf import settings
from django.db.models import Q
from projects.helpers import get_minio_keys
from django.core import serializers
from .helpers import create_user_settings
from api.serializers import ProjectSerializer
from rest_framework.renderers import JSONRenderer
import json
import yaml

@login_required
def index(request, user, project):
    template = 'labs/index.html'
    project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()
    sessions = Session.objects.filter(Q(project=project), Q(lab_session_owner=request.user)).order_by('-created_at')
    all_user_sess = Session.objects.filter(Q(lab_session_owner=request.user))

    # exclude_gpu = False
    # for user_sess in all_user_sess:
    #     if user_sess.flavor_slug == 'gpu':
    #         exclude_gpu = True
    #         message = "You are only allowed to have one GPU session running at a time. You will not be able to create a new GPU session until you delete your existing GPU session."

    # if not exclude_gpu:
    flavors = Flavor.objects.all()
    # else:
    #     flavors = Flavor.objects.filter(Q(name=='CPU'))
    environments = Environment.objects.all()
    cluster = Cluster.objects.get(name=project.cluster)
    url = cluster.base_url

    return render(request, template, locals())


@login_required
def run(request, user, project):
    project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()

    if request.method == "POST":
        uid = uuid.uuid4()
        name = str(project.slug) + str(uid)[0:7]
        flavor_slug = request.POST.get('flavor', None)
        environment_slug = request.POST.get('environment', None)
        
        lab_instance = Session(name=name,
                               id=uid,
                               flavor_slug=flavor_slug,
                               environment_slug=environment_slug,
                               project=project,
                               lab_session_owner=request.user)
        lab_instance.save()

    return HttpResponseRedirect(
        reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))


@login_required
def delete(request, user, project, id):
    project = Project.objects.filter(Q(slug=project), Q(owner=request.user) | Q(authorized=request.user)).first()
    session = Session.objects.filter(Q(id=id), Q(project=project), Q(lab_session_owner=request.user)).first()

    if session:
        session.helmchart.delete()

    return HttpResponseRedirect(
        reverse('labs:index', kwargs={'user': request.user, 'project': str(project.slug)}))
