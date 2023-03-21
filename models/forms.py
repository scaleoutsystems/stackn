from django import forms

from .models import Metadata, Model, ModelLog

RELEASE_TYPE_CHOICES = (("M", "Major"), ("m", "Minor"))
ACCESS_CHOICES = (
    ("PR", "Private"),
    ("LI", "Limited"),
    ("PU", "Public"),
)


class ModelForm(forms.ModelForm):
    release_type = forms.ChoiceField(
        label="Release type",
        choices=RELEASE_TYPE_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    access = forms.ChoiceField(
        label="Access",
        choices=ACCESS_CHOICES,
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    path_field = Model._meta.get_field("path")
    path_default = path_field.default

    path = forms.CharField(
        label="Path",
        help_text="Current folder name of your trained model*",
        required=True,
        initial=path_default,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = Model
        fields = (
            "name",
            "description",
            "release_type",
            "version",
            "access",
            "path",
        )


class ModelLogForm(forms.ModelForm):
    class Meta:
        model = ModelLog
        fields = (
            "run_id",
            "trained_model",
            "project",
            "training_started_at",
            "execution_time",
            "code_version",
            "current_git_repo",
            "latest_git_commit",
            "system_details",
            "cpu_details",
            "training_status",
        )


class Metadata(forms.ModelForm):
    class Meta:
        model = Metadata
        fields = (
            "run_id",
            "trained_model",
            "project",
            "model_details",
            "parameters",
            "metrics",
        )


class UploadModelCardHeadlineForm(forms.Form):
    file = forms.ImageField()


class EnvironmentForm(forms.Form):
    registry = forms.CharField(label="Registry DNS", max_length=100)
    username = forms.CharField(label="Username", max_length=100)
    repository = forms.CharField(label="Repository", max_length=100)
    image = forms.CharField(label="Image", max_length=100)
    tag = forms.CharField(label="Tag", max_length=100)
