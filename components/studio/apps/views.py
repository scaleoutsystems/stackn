from django.shortcuts import render, HttpResponseRedirect, reverse
from .models import Apps, AppInstance
from projects.models import Project

# Create your views here.
def index(request, user, project):
    template = 'index_apps.html'
    apps = Apps.objects.all()
    project = Project.objects.get(slug=project)

    appinstances = AppInstance.objects.filter(owner=request.user)
    apps_installed = False
    if appinstances:
        apps_installed = True
        
    # try:
    #     projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user)).distinct('pk')
    # except TypeError as err:
    #     projects = []
    #     print(err)
    
    # request.session['next'] = '/projects/'
    return render(request, template, locals())

def create(request, user, project, app_slug):
    template = 'create.html'
    project = Project.objects.get(slug=project)
    app = Apps.objects.get(slug=app_slug)
    if request.method == "POST":

        instance = AppInstance(app=app, project=project, settings=request.POST.get('settings', None), owner=request.user)
        instance.save()

        return HttpResponseRedirect(
                reverse('apps:index', kwargs={'user': request.user, 'project': str(project.slug)}))
    # try:
    #     projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user)).distinct('pk')
    # except TypeError as err:
    #     projects = []
    #     print(err)
    
    # request.session['next'] = '/projects/'
    return render(request, template, locals())

def delete(request, user, project, ai_id):
    # print(appinstance)
    appinstance = AppInstance.objects.get(pk=ai_id)
    appinstance.helmchart.delete()
    return HttpResponseRedirect(
                reverse('apps:index', kwargs={'user': request.user, 'project': str(project)}))