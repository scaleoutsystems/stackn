from django import forms
from django.contrib.auth.models import User


class TransferProjectOwnershipForm(forms.Form):
    transfer_to = forms.CharField(label='New project owner', max_length=256)


class PublishProjectToGitHub(forms.Form):
    user_name = forms.CharField(label='GitHub username', max_length=256)
    user_password = forms.CharField(label='GitHub password', widget=forms.PasswordInput(), max_length=256)


class GrantAccessForm(forms.Form):
    platform_users = User.objects.all()

    OPTIONS = []
    for user in platform_users:
        OPTIONS.append((user.pk, user.username))

    selected_users = forms.MultipleChoiceField(widget=forms.SelectMultiple, choices=OPTIONS)
