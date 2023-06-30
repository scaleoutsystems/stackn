from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# Sign Up Form
class SignUpForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        required=True,
        label=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username*"}
        ),
    )
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "First name"}
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Last name"}
        ),
    )
    email = forms.EmailField(
        max_length=254,
        label=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Email*"}
        ),
    )
    password1 = forms.CharField(
        label=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password*"}
        ),
    )
    password2 = forms.CharField(
        label=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Confirm"}
        ),
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2',
        ]
