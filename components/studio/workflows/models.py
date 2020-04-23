from django.db import models
from yamlfield.fields import YAMLField
import uuid


class WorkflowDefinition(models.Model):
    name = models.CharField(max_length=512, unique=True)
    definition = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)
    # TODO add capabilities to set the input/output parameters that are required to run workflow


class WorkflowInstance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    CREATED = 'CR'
    STARTED = 'ST'
    STOPPED = 'SP'
    FINISHED = 'FN'
    ABORTED = 'AB'
    STATUS = [
        (CREATED, 'Created'),
        (STARTED, 'Started'),
        (STARTED, 'Stopped'),
        (FINISHED, 'Finished'),
        (ABORTED, 'Aborted'),
    ]
    project = models.ForeignKey('projects.Project', on_delete=models.DO_NOTHING, related_name='project')
    status = models.CharField(max_length=2, choices=STATUS, default=CREATED)

    workflow = models.ForeignKey('workflows.WorkflowDefinition', on_delete=models.DO_NOTHING,
                                 related_name='workflow_definition')
    name = models.CharField(max_length=512, unique=False)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now=True)
    # TODO add capability bindings to input/output parameters and the set values for each that is intended to run.

