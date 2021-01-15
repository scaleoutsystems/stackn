from django.shortcuts import render
from datetime import datetime, timedelta
from .models import ActivityLog

def index(request):
    activity_logs = ActivityLog.objects.filter(user=request.user).order_by('-created_at')[:5]

    return render(request, 'studio_admin_index.html', locals())
