from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import RequestAccount
from models.models import Model
import modules.keycloak_lib as kc
from projects.models import Project, S3, Flavor, ProjectTemplate, MLFlow
from django.db.models import Q
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import datetime


# Since this is a production feature, it will only work if DEBUG is set to False
def handle_page_not_found(request, exception):
    return HttpResponseRedirect('/')

def handle_500(request):
    template = '500.html'
    return render(request, template, locals())

def home(request):
    menu = dict()
    menu['home'] = 'active'
    base_template = 'base.html'
    if 'project' in request.session:
        print("HEREEEEE")
        project_slug = request.session['project']
        is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
        if is_authorized:
            try:
                project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
                base_template = 'baseproject.html'
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
    template = 'home.html'
    return render(request, template, locals())

def account(request):
    return render(request, 'account.html', locals())

def request_account(request):
    # previous = model.get_access_display()
    base_template = 'base.html'
    if 'project' in request.session:
        print("HEREEEEE")
        project_slug = request.session['project']
        is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
        if is_authorized:
            try:
                project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
                base_template = 'baseproject.html'
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
    if request.method == 'POST':
        print("New Account Request: ",request.POST)
        request_account = RequestAccount(fname=request.POST['fname'],lname=request.POST['lname'],email=request.POST['email'],org=request.POST['org'],deployed=request.POST['deployed'],use=request.POST['use'],resources=request.POST['resources'])
        request_account.save()
        email_body = render_to_string("admin_email.txt", 
        { 
            "fname": request.POST['fname'],
            "lname": request.POST['lname'],
            "email": request.POST['email'],
            "org": request.POST['org'],
            "deployed": request.POST['deployed'],
            "use": request.POST['use'],
            "resources": request.POST['resources'],
            "date_received": datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)")
        })
        print(email_body)
        send_mail(
            'New User Registeration Request (SciLifeLab Serve)',
            email_body,
            'SciLifeLab Serve',
            ['hamza.saeed@scilifelab.uu.se'],
            fail_silently=False,
        )
    return render(request, 'home.html', locals())

def guide(request):
    menu = dict()
    menu['guide'] = 'active'
    base_template = 'base.html'
    if 'project' in request.session:
        project_slug = request.session['project']
        is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
        if is_authorized:
            try:
                project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
                base_template = 'baseproject.html'
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
    template = 'user_guide.html'
    return render(request, template , locals())

def privacy(request):
    base_template = 'base.html'
    if 'project' in request.session:
        project_slug = request.session['project']
        is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
        if is_authorized:
            try:
                project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
                base_template = 'baseproject.html'
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
    return render(request, 'privacy.html', locals())

def about(request):
    menu = dict()
    menu['about'] = 'active'
    base_template = 'base.html'
    if 'project' in request.session:
        project_slug = request.session['project']
        is_authorized = kc.keycloak_verify_user_role(request, project_slug, ['member'])
        if is_authorized:
            try:
                project = Project.objects.filter(Q(owner=request.user) | Q(authorized=request.user), status='active', slug=project_slug).first()
                base_template = 'baseproject.html'
            except Exception as err:
                project = []
                print(err)
            if not project:
                base_template = 'base.html'
    return render(request, 'about.html', locals())
