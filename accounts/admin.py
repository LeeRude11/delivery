from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User
from .forms import UserChangeForm, UserCreationForm


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = (
        'phone_number',
        'first_name',
        'second_name',
        'email',
        'date_of_birth',
        'street',
        'house',
        'apartment',
        'date_of_birth',
        'is_admin'
    )
    list_filter = ('is_admin',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'second_name', 'email', 'date_of_birth',)
            }),
        ('Address', {
            'fields': ('street', 'house', 'apartment',)
            }),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number',
                'password1',
                'password2',
                'first_name',
                'second_name',
                'email',
                'date_of_birth',
                'street',
                'house',
                'apartment',
                'date_of_birth',
            )
        }),
    )
    search_fields = ('phone_number',)
    ordering = ('phone_number',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
