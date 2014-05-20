from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group
from users.models import OCUser, Membership, Invitation


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = OCUser
        fields = ('email', 'display_name')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField(label=_("Password"),
        help_text=_("Raw passwords are not stored, so there is no way to see "
                    "this user's password, but you can change the password "
                    "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = OCUser

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserMembershipInline(admin.TabularInline):
    model = Membership
    fk_name = 'user'

class MembershipAdmin(admin.ModelAdmin):

    list_display = (
                    'community',
                    'default_group_name',
                    'user',
                    'created_at',
                    )
    
    list_filter = ('community', 'default_group_name',)
    
class OCUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'display_name', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'is_active')}),
        ('Personal info', {'fields': ('display_name',)}),
        ('Permissions', {'fields': ('is_superuser', 'is_staff')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    inlines = [UserMembershipInline]

admin.site.register(OCUser, OCUserAdmin)
admin.site.unregister(Group)

admin.site.register(Membership, MembershipAdmin)

class InvitationAdmin(admin.ModelAdmin):
    list_display = ('community', 'name', 'email', 'default_group_name', 'last_sent_at', 'status')
    ordering = ('community', 'last_sent_at')

admin.site.register(Invitation, InvitationAdmin)

