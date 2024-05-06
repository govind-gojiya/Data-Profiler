from django import forms

class RegisterForm(forms.Form):
    name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)