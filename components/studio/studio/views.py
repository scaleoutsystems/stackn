from django.http import HttpResponseRedirect
from django.http import HttpResponse
from projects.models import Project

# Since this is a production feature, it will only work if DEBUG is set to False
def handle_page_not_found(request, exception):
    return HttpResponseRedirect('/')

def auth(request):
    if request.user.is_authenticated:
        project_slug = request.GET.get('project')
        project = Project.objects.get(slug=project_slug)
        if request.user.has_perm('can_view_project', project):
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=403)
    return HttpResponse(status=401)