from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import RequestAccount
from models.models import Model

# Since this is a production feature, it will only work if DEBUG is set to False
def handle_page_not_found(request, exception):
    return HttpResponseRedirect('/')

def home(request):
    menu = dict()
    menu['home'] = 'active'
    return render(request, 'home.html', locals())

def account(request):
    return render(request, 'account.html', locals())

def request_account(request):
    # previous = model.get_access_display()
    if request.method == 'POST':
        print("New Account Request: ",request.POST)
        request_account = RequestAccount(fname=request.POST['fname'],lname=request.POST['lname'],email=request.POST['email'],org=request.POST['org'],deployed=request.POST['deployed'],use=request.POST['use'],resources=request.POST['resources'])
        request_account.save()
    return render(request, 'home.html', locals())
