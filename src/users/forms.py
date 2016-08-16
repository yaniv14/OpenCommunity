from communities.models import CommunityGroup, GroupUser
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, gettext
from ocd.formfields import HTMLArea, GroupCheckboxSelectMultiple
import floppyforms.__future__ as forms
from users.models import Invitation, OCUser

LOGIN_ERROR = _("Please enter a correct %(username)s and password. "
                "Note that both fields may be case-sensitive.")


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation

        fields = (
            'name',
            'email',
            'groups',
            'message',
        )

        widgets = {
            'name': forms.TextInput,
            'email': forms.EmailInput,
            'message': HTMLArea,
            'groups': GroupCheckboxSelectMultiple
        }

    def clean(self):
        cleaned_data = super(InvitationForm, self).clean()
        groups = cleaned_data.get("groups")
        email = cleaned_data.get("email")
        if GroupUser.objects.filter(user__email=email, group_id__in=groups).exists():
            raise forms.ValidationError(_("This user already a member of this community."))
        if Invitation.objects.filter(email=email, groups__in=groups).exists():
            raise forms.ValidationError(_("This user is already invited to this community."))
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        try:
            validate_email(email)
        except ValidationError as e:
            raise forms.ValidationError(_("Form error. Please supply a valid email."))
        return email.lower()

    def __init__(self, community=None, *args, **kwargs):
        super(InvitationForm, self).__init__(*args, **kwargs)
        self.fields['groups'].queryset = CommunityGroup.objects.filter(community=community)


class QuickSignupForm(forms.ModelForm):
    password1 = forms.CharField(label=_('Password'), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'), widget=forms.PasswordInput)

    class Meta:
        model = OCUser

        fields = (
            'display_name',
        )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super(QuickSignupForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        # Temp solution for 'last_login' field can be null in Django 1.8
        user.last_login = timezone.now()
        if commit:
            user.save()
        return user


class OCPasswordResetForm(PasswordResetForm):
    class Meta:
        fields = (
            'email',
        )

    def __init__(self, *args, **kwargs):
        super(OCPasswordResetForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['class'] = u'form-control'


class OCPasswordResetConfirmForm(SetPasswordForm):
    class Meta:
        fields = (
            'new_password1',
            'new_password2',
        )

    def __init__(self, *args, **kwargs):
        super(OCPasswordResetConfirmForm, self).__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs['class'] = u'form-control'
        self.fields['new_password2'].widget.attrs['class'] = u'form-control'


class ImportInvitationsForm(forms.Form):
    csv_file = forms.FileField(required=True)

    def __init__(self, *args, **kwargs):
        super(ImportInvitationsForm, self).__init__(*args, **kwargs)
        self.fields['csv_file'].label = _("Upload CSV file to import")


class MembersGroupsForm(forms.Form):
    groups = forms.MultipleChoiceField(widget=GroupCheckboxSelectMultiple, label=_('Choose groups'))
    members = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, community=None, *args, **kwargs):
        super(MembersGroupsForm, self).__init__(*args, **kwargs)
        self.fields['groups'].choices = ((x.id, gettext(x.title)) for x in community.groups.all())

    def save(self):
        pass


class MembersCommunityRemoveForm(forms.Form):
    members = forms.CharField(widget=forms.HiddenInput())

    def save(self):
        pass
