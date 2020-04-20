from django.db import models


class ReportGenerator(models.Model):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    generator = models.CharField(max_length=256)
    visualiser = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)


class Report(models.Model):
    REPORT_STATUS = [
        ('I', 'Initiated'),
        ('P', 'Processing'),
        ('C', 'Completed'),
        ('F', 'Failed'),
    ]
    model = models.ForeignKey('models.Model', on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    report = models.TextField(blank=True)
    job_id = models.CharField(max_length=256)
    generator = models.ForeignKey('reports.ReportGenerator', on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=REPORT_STATUS, default='I')
