from communities.models import CommunityGroupRole
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group
from users.models import OCUser, Invitation, CommunityMembership, CommitteeMembership


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
        fields = '__all__'

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserCommunityMembershipInline(admin.TabularInline):
    model = CommunityMembership
    fk_name = 'user'
    extra = 1


class UserCommitteeMembershipInline(admin.TabularInline):
    model = CommitteeMembership
    fk_name = 'user'
    extra = 1


class CommunityMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'community',
        'display_user_email',
        'user',
        'created_at',
    )

    list_filter = ('community', 'user__email', 'user')
    ordering = ['community', ]

    def display_user_email(self, obj):
        return obj.user.email

    display_user_email.short_description = _('Email')


class CommitteeMembershipAdmin(admin.ModelAdmin):
    list_display = (
        'committee',
        'display_user_email',
        'user',
        'display_group',
        'display_role',
        'created_at',
    )

    list_filter = ('committee', 'user__email', 'user')
    ordering = ['committee', ]

    def display_user_email(self, obj):
        return obj.user.email

    display_user_email.short_description = _('Email')

    def display_role(self, obj):
        return obj.role.title

    display_role.short_description = _('Role')

    def display_group(self, obj):
        try:
            cgr = CommunityGroupRole.objects.get(role=obj.role, committee=obj.committee)
        except CommunityGroupRole.DoesNotExist:
            cgr = None
        return cgr.group.title if cgr else ''

    display_group.short_description = _('Group')


class OCUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('email', 'display_name')
    list_filter = ()
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

    inlines = [UserCommunityMembershipInline, UserCommitteeMembershipInline]

    # def get_groups(self, obj):
    #     memberships = obj.memberships.all().values_list('group_name_id', flat=True)
    #     groups = CommunityGroupRole.objects.filter(group_id__in=memberships)
    #     l = []
    #     for g in groups:
    #         l.append(u'{0}: {1}'.format(g.group.title, g.committee.name))
    #     return " | ".join(l)
    #
    # get_groups.short_description = _('Committee & Groups')


admin.site.register(OCUser, OCUserAdmin)
admin.site.unregister(Group)

admin.site.register(CommunityMembership, CommunityMembershipAdmin)
admin.site.register(CommitteeMembership, CommitteeMembershipAdmin)


class InvitationAdmin(admin.ModelAdmin):
    list_display = ('community', 'name', 'email', 'get_groups', 'last_sent_at', 'status')
    ordering = ('community', 'last_sent_at')

    def get_groups(self, obj):
        return ", ".join([g.title for g in obj.groups.all()])


admin.site.register(Invitation, InvitationAdmin)
