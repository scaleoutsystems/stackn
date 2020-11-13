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
        fields = (
            'uid', 'trained_model', 'training_started_at', 'execution_time', 'current_git_commit', 
            'current_git_repo', 'system_info', 'cpu_info', 'training_status', 'miscellaneous')