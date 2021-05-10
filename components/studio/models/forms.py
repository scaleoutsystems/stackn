from django import forms
from .models import Model, ModelLog, Metadata


class ModelForm(forms.ModelForm):
    class Meta:
        model = Model
        fields = ('uid', 'name', 'description', 'url', 'project')
        widgets = {
            'uid': forms.HiddenInput(),
            'project': forms.HiddenInput()
        }

class ModelLogForm(forms.ModelForm):
    class Meta:
        model = ModelLog
        fields = (
            'run_id', 'trained_model', 'project', 'training_started_at', 'execution_time', 'code_version',
            'current_git_repo', 'latest_git_commit', 'system_details', 'cpu_details', 'training_status')

class Metadata(forms.ModelForm):
    class Meta:
        model = Metadata
        fields = (
            'run_id', 'trained_model', 'project', 'model_details', 'parameters', 'metrics')

class UploadModelImageForm(forms.Form):
    file = forms.ImageField()
