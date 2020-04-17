from django.db import models


class Model(models.Model):
    CREATED = 'CR'
    DEPLOYED = 'DP'
    STATUS = [
        (CREATED, 'Created'),
        (DEPLOYED, 'Deployed'),
    ]
    uid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    resource = models.URLField(max_length=2048)
    url = models.URLField(max_length=512, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey('projects.Project', on_delete=models.DO_NOTHING, related_name='model_owner')
    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)
    tag = models.CharField(max_length=10, default='latest')

    def __str__(self):
        return "{name}".format(name=self.name)

