from django import forms
from .models import DeploymentDefinition, DeploymentInstance


class DeploymentDefinitionForm(forms.ModelForm):
    class Meta:
        model = DeploymentDefinition
        fields = ('name',)


class DeploymentInstanceForm(forms.ModelForm):
    class Meta:
        model = DeploymentInstance
        fields = ('model', 'access', 'deployment')

class PredictForm(forms.Form):
    file = forms.FileField()