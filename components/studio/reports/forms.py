from django import forms
from .models import ReportGenerator


class GenerateReportForm(forms.Form):
    generator_file = forms.CharField(label='Path to file', max_length=100)


class ReportGeneratorForm(forms.ModelForm):
    class Meta:
        model = ReportGenerator
        fields = ('project', 'description', 'generator', 'visualiser')
        widgets = {
            'project': forms.HiddenInput()
        }
