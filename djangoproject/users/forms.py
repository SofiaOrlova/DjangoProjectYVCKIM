from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.forms import (
    UserCreationForm as DjangoUserCreationForm,
    AuthenticationForm as DjangoAuthenticationForm,
)
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from users.utils import send_email_for_verify


User = get_user_model()

class AuthenticationForm(DjangoAuthenticationForm):

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

            if not self.user_cache.email_verify:
                send_email_for_verify(self.request, self.user_cache)
                raise ValidationError(
                    'Email not verify, check your email',
                    code='invalid_login',
                )

        return self.cleaned_data


class UserCreationForm(DjangoUserCreationForm):
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
        
    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")