from django import forms

class PostgresForm(forms.Form):
    hostname = forms.CharField(label="Host name:", max_length=100)
    portnumber = forms.IntegerField(label="Port:", initial=5432)
    username = forms.CharField(label="User name:", max_length=100)
    password = forms.CharField(label="Password:", max_length=100)
    database_name = forms.CharField(label="Database name:", max_length=100)
