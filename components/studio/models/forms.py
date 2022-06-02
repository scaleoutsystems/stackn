from django import forms

from .models import Metadata, Model, ModelLog


class ModelForm(forms.ModelForm):
    class Meta:
        model = Model
        fields = ('name', 'description', 'release_type',
                  'version', 'access', 'path')
        labels = {
            'path': ('Current folder name of your trained model*'),
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


class UploadModelCardHeadlineForm(forms.Form):
    file = forms.ImageField()


class EnvironmentForm(forms.Form):
    registry = forms.CharField(label='Registry DNS', max_length=100)
    username = forms.CharField(label='Username', max_length=100)
    repository = forms.CharField(label='Repository', max_length=100)
    image = forms.CharField(label='Image', max_length=100)
    tag = forms.CharField(label='Tag', max_length=100)
