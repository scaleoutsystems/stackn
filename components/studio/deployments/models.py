from django.db import models


class DeploymentDefinition(models.Model):
    project = models.ForeignKey('projects.Project',
                                on_delete=models.DO_NOTHING,
                                related_name='project_owner')
    name = models.CharField(max_length=512, unique=True)
    bucket = models.CharField(max_length=512)
    filename = models.CharField(max_length=512)
    path_predict = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}".format(self.name)


class DeploymentInstance(models.Model):
    PRIVATE = 'PR'
    LIMITED = 'LI'
    PUBLIC = 'PU'
    ACCESS = [
        (PRIVATE, 'Private'),
        (LIMITED, 'Limited'),
        (PUBLIC, 'Public'),
    ]

    deployment = models.ForeignKey('deployments.DeploymentDefinition', on_delete=models.DO_NOTHING)

    model = models.OneToOneField('models.Model', on_delete=models.DO_NOTHING, related_name='deployed_model', unique=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    endpoint = models.CharField(max_length=512)
    release = models.CharField(max_length=512)
    # sample_input = models.TextField(blank=True, null=True)
    # sample_output = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}:{}".format(self.model.name, self.model.tag)

