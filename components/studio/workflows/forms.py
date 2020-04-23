from django import forms
from .models import WorkflowDefinition, WorkflowInstance


class WorkflowDefinitionForm(forms.ModelForm):
    class Meta:
        model = WorkflowDefinition
        fields = ('name', 'definition')


class WorkflowInstanceForm(forms.ModelForm):
    class Meta:
        model = WorkflowInstance
        fields = ('name', 'workflow', 'project', 'status')
        attrs = {'class': 'form-control'}
