from django import forms

class SnowflakeForm(forms.Form):
    account_identifier = forms.CharField(max_length=100)
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)
    database_name = forms.CharField(label="Database name:", max_length=100)
