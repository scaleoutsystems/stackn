from django.shortcuts import render
from datetime import datetime, timedelta
from .models import ActivityLog

def index(request):
    return render(request, 'studio_admin_index.html', locals())

def load_recent_activity(request):
    template = 'recent_activity.html'

    time_period = request.GET.get('period')
    if time_period == 'week':
        last_week = datetime.today() - timedelta(days=7)
        activity_logs = ActivityLog.objects.filter(created_at__gte=last_week).order_by('-created_at')
    elif time_period == 'month':
        last_month = datetime.today() - timedelta(days=30)
        activity_logs = ActivityLog.objects.filter(created_at__gte=last_month).order_by('-created_at')
    else:
        activity_logs = ActivityLog.objects.all().order_by('-created_at')

    return render(request, template, {'activity_logs': activity_logs})
