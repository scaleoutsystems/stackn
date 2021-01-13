from django.shortcuts import render

def index(request):
    return render(request, 'studio_admin_index.html', locals())
