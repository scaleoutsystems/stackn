from django import forms


class TransferProjectOwnershipForm(forms.Form):
    transfer_to = forms.CharField(label='New project owner', max_length=256)


class PublishProjectToGitHub(forms.Form):
    user_name = forms.CharField(label='GitHub username', max_length=256)
    user_password = forms.CharField(label='GitHub password', max_length=256)
