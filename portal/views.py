from django.apps import apps
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import View

AppInstance = apps.get_model(app_label=settings.APPINSTANCE_MODEL)
Project = apps.get_model(app_label=settings.PROJECTS_MODEL)


def index(request, id=0):
    try:
        projects = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status="active")
    except Exception:
        print("User not logged in.")
    if "project" in request.session:
        project_slug = request.session["project"]

    media_url = settings.MEDIA_URL

    # create session object to store info about app and their tag counts
    if "app_tags" not in request.session:
        request.session["app_tags"] = {}
    # tag_count from the get request helps set num_tags
    # which helps set the number of tags to show in the template
    if "tag_count" in request.GET:
        # add app id to app_tags object
        if "app_id_add" in request.GET:
            num_tags = int(request.GET["tag_count"])
            id = int(request.GET["app_id_add"])
            request.session["app_tags"][str(id)] = num_tags
        # remove app id from app_tags object
        if "app_id_remove" in request.GET:
            num_tags = int(request.GET["tag_count"])
            id = int(request.GET["app_id_remove"])
            if str(id) in request.session["app_tags"]:
                request.session["app_tags"].pop(str(id))

    # reset app_tags if Apps Tab on Sidebar pressed
    if id == 0:
        if "tf_add" not in request.GET and "tf_remove" not in request.GET:
            request.session["app_tags"] = {}

    published_apps = AppInstance.objects.filter(~Q(state="Deleted"), access="public")

    # create session object to store ids for tag seacrh if it does not exist
    if "app_tag_filters" not in request.session:
        request.session["app_tag_filters"] = []
    if "tf_add" in request.GET:
        tag = request.GET["tf_add"]
        if tag not in request.session["app_tag_filters"]:
            request.session["app_tag_filters"].append(tag)
    elif "tf_remove" in request.GET:
        tag = request.GET["tf_remove"]
        if tag in request.session["app_tag_filters"]:
            request.session["app_tag_filters"].remove(tag)
    elif "tag_count" not in request.GET:
        tag = ""
        request.session["app_tag_filters"] = []
    print("app_tag_filters: ", request.session["app_tag_filters"])

    # changed list of published model only if tag filters are present
    if request.session["app_tag_filters"]:
        tagged_published_apps = []
        for app in published_apps:
            for t in app.tags.all():
                if t in request.session["app_tag_filters"]:
                    tagged_published_apps.append(app)
                    break
        published_apps = tagged_published_apps

    request.session.modified = True

    template = "portal/index.html"
    return render(request, template, locals())


class HomeView(View):
    template = "portal/home.html"

    def get(self, request):
        return render(request, self.template, locals())


def about(request):
    template = "portal/about.html"
    return render(request, template, locals())


def teaching(request):
    template = "portal/teaching.html"
    return render(request, template, locals())
