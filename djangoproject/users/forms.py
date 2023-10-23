from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label = ("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    first_name = forms.CharField(widget=forms.TextInput(attrs={ 'class': 'form-control' }))
    last_name = forms.CharField(widget=forms.TextInput(attrs={ 'class': 'form-control' }))
    username = forms.CharField(widget=forms.TextInput(attrs={ 'class': 'form-control' }))
    email = forms.CharField(widget=forms.EmailInput(attrs={ 'class': 'form-control' }))
    # username = forms.CharField(widget=forms.TextInput(attrs={
    #     'class': 'form-control' }))
    # password = forms.CharField(widget=forms.PasswordInput(attrs={
    #     'class': 'form-control'}))
        
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")