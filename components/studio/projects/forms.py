from django import forms


class TransferProjectOwnershipForm(forms.Form):
    transfer_to = forms.CharField(label='New project owner', max_length=256)
