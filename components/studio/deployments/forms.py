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
    pred_request = forms.FileField()

class SettingsForm(forms.Form):
    replicas = forms.IntegerField(min_value=1, max_value=25, label="Replicas")
    limits_cpu = forms.IntegerField()
    limits_memory = forms.IntegerField()
    requests_cpu = forms.IntegerField()
    requests_memory = forms.IntegerField()
