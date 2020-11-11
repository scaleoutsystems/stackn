from django import forms
from .models import Model, ModelLog


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
        fields = ('model_to_log', 'run_id', 'run_created_at', 'run_duration', 'current_git_commit', 'current_git_repo', 'status')