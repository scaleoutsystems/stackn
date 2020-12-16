from django import forms
from .datasheet_questions import q

class DatasheetForm(forms.Form):
    q1 = forms.CharField(label=q[0], max_length=100, widget=forms.Textarea({}))
    q2 = forms.CharField(label=q[1], max_length=100, widget=forms.Textarea({}))