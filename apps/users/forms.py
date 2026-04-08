from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginFormCustom(AuthenticationForm):
    username = forms.CharField(
        label="Email o DNI", # Este es el texto que aparecerá
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'autocapitalize': 'none',
            'autocomplete': 'username',
        })
    )