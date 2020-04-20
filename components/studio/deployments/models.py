from django.db import models


class DeploymentDefinition(models.Model):
    name = models.CharField(max_length=512, unique=True)
    definition = models.TextField()
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

    deployment = models.ForeignKey('deployments.DeploymentDefinition', on_delete=models.DO_NOTHING,
                                   related_name='deployment_definition')

    model = models.ForeignKey('models.Model', on_delete=models.DO_NOTHING, related_name='deployed_model')
    name = models.CharField(max_length=512, unique=True)
    access = models.CharField(max_length=2, choices=ACCESS, default=PRIVATE)
    endpoint = models.URLField()
    sample_input = models.TextField(blank=True, null=True)
    sample_output = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=512, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}:{}".format(self.name, self.version)
