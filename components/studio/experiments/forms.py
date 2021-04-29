from django import forms
from .models import Experiment


class ExperimentForm(forms.ModelForm):
    schedule = forms.CharField(max_length=128, required=False)
    class Meta:
        model = Experiment
        fields = ('command', 'environment', 'schedule')
