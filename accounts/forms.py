from django import forms
from django.contrib.auth.forms import (
    ReadOnlyPasswordHashField, AuthenticationForm)
from django.utils.translation import gettext_lazy as _

import re
from .models import User
EMAIL_CHECK = '@'


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = (
            'phone_number',
            'first_name',
            'second_name',
            'email',
            'date_of_birth',
            'street',
            'house',
            'apartment'
        )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        # store email in lowercase
        email = self.cleaned_data.get("email")
        if email:
            email = email.lower()
        return email

    def clean_phone_number(self):
        # store only digits of phone numbers
        phone_number = self.cleaned_data.get("phone_number")
        return re.sub('\D', '', phone_number)

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = (
            'phone_number',
            'password',
            'first_name',
            'second_name',
            'email',
            'date_of_birth',
            'street',
            'house',
            'apartment',
            'is_active',
            'is_admin'
        )

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class CustomAuthForm(AuthenticationForm):
    """A form for logging in with password and either email or phone number.
    """
    error_messages = {
        'invalid_login': _(
            "Please enter a correct phone number (or email) and password."
        ),
        'inactive': _("This account is inactive."),
    }

    def clean_username(self):
        # store only digits of phone numbers
        username = self.cleaned_data.get("username")
        if EMAIL_CHECK in username:
            return username.strip().lower()
        else:
            return re.sub('\D', '', username)
