from datetime import datetime, date, time

from communities.models import Committee, CommunityGroup, CommunityGroupRole
from django.utils.translation import ugettext_lazy as _, gettext
from ocd.formfields import HTMLArea, OCCheckboxSelectMultiple, OCSplitDateTimeField
import floppyforms.__future__ as forms
from haystack.forms import ModelSearchForm


class EditUpcomingMeetingForm(forms.ModelForm):
    class Meta:
        model = Committee

        fields = (
            'upcoming_meeting_title',
            'upcoming_meeting_location',
            'upcoming_meeting_scheduled_at',
            # 'voting_ends_at',
            'upcoming_meeting_comments',
        )

        widgets = {
            'upcoming_meeting_title': forms.TextInput,
            'upcoming_meeting_location': forms.TextInput,
            # 'voting_ends_at': OCSplitDateTime,
            'upcoming_meeting_comments': HTMLArea,
        }

        field_classes = {
            'upcoming_meeting_scheduled_at': OCSplitDateTimeField,
        }

    def __init__(self, *args, **kwargs):
        super(EditUpcomingMeetingForm, self).__init__(*args, **kwargs)
        self.fields['upcoming_meeting_title'].label = _('Title')
        self.fields['upcoming_meeting_scheduled_at'].label = _('Scheduled at')
        self.fields['upcoming_meeting_location'].label = _('Location')
        self.fields['upcoming_meeting_comments'].label = _('Background')

    """
    removed this function as we don't include voting_end_time in the form any more.
    # ----------------------------------------------------------------------------
    def clean(self):
        #prevent voting end time from illegal values (past time,
        #time after meeting schedule)
        
        try:
            voting_ends_at = self.cleaned_data['voting_ends_at']
        except KeyError:
            voting_ends_at = None
        try:
            meeting_time = self.cleaned_data['upcoming_meeting_scheduled_at']
        except KeyError:
            meeting_time = None

        if voting_ends_at:
            if voting_ends_at <= timezone.now():
                raise forms.ValidationError(_("End voting time cannot be set to the past"))
            if meeting_time and voting_ends_at > meeting_time:
                raise forms.ValidationError(_("End voting time cannot be set to after the meeting time"))
        return self.cleaned_data
    """

    def save(self):
        c = super(EditUpcomingMeetingForm, self).save()
        c.voting_ends_at = datetime.combine(date(2025, 1, 1), time(12, 0, 0))
        c.save()
        return c


class PublishUpcomingMeetingForm(forms.ModelForm):
    me = forms.BooleanField(label=_("Me only"), widget=forms.CheckboxInput, required=False)
    send_to = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(), required=False)

    class Meta:
        model = CommunityGroup

        fields = ()


class EditUpcomingMeetingSummaryForm(forms.ModelForm):
    class Meta:
        model = Committee

        fields = (
            'upcoming_meeting_summary',
        )

        widgets = {
            'upcoming_meeting_summary': HTMLArea,
        }


class UpcomingMeetingParticipantsForm(forms.ModelForm):
    class Meta:
        model = Committee

        fields = (
            'upcoming_meeting_participants',
            'upcoming_meeting_guests',
        )

        widgets = {
            'upcoming_meeting_participants': OCCheckboxSelectMultiple,
            'upcoming_meeting_guests': forms.Textarea,
        }

        # def __init__(self, *args, **kwargs):
        #     super(UpcomingMeetingParticipantsForm, self).__init__(*args, **kwargs)
        #     participants = self.instance.upcoming_meeting_participants.values_list(
        #         'id', flat=True)
        #     board_in = []
        #     board_choices = []
        #     # for b in self.instance.get_board_members():
        #     for b in self.instance.get_community_participant_members():
        #         board_choices.append((b.id, b.display_name,))
        #         if b.id in participants:
        #             board_in.append(b.id)
        #     self.fields['board'].choices = board_choices
        #     self.initial['board'] = board_in
        #     self.fields['upcoming_meeting_participants'].queryset = self.instance.get_members()
        #     self.fields['upcoming_meeting_participants'].label = ""


class CommunitySearchForm(ModelSearchForm):
    pass
    # def search(self):
    # # First, store the SearchQuerySet received from other processing.
    #     sqs = super(DateRangeSearchForm, self).search()
    #
    #     if not self.is_valid():
    #         return self.no_query_found()
    #
    #     return sqs


class GroupForm(forms.ModelForm):
    class Meta:
        model = CommunityGroup

        fields = (
            'title',
        )

        widgets = {
            'title': forms.TextInput,
        }

    def __init__(self, community=None, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        self.group_role = GroupRoleForm(community=community, prefix='group_role',
                                        data=self.data if self.is_bound else None)
        self.group_role.fields['role'].required = False
        self.group_role.fields['committee'].required = False
        self.group_role.fields.pop('group')

    def is_valid(self):
        valid = super(GroupForm, self).is_valid()
        if not self.data.get('group') or not self.data.get('role') or not self.data.get('committee'):
            return valid
        return self.group_role.is_valid() and valid

    def save(self, commit=True):
        o = super(GroupForm, self).save(commit)
        if self.data.get('committee') and self.data.get('role'):
            self.group_role.instance.group = o
            self.group_role.save()
        return o


class GroupRoleForm(forms.ModelForm):
    class Meta:
        model = CommunityGroupRole

        fields = (
            'group',
            'role',
            'committee'
        )

    def __init__(self, community=None, *args, **kwargs):
        super(GroupRoleForm, self).__init__(*args, **kwargs)
        self.fields['group'].queryset = community.groups.all()
        self.fields['role'].queryset = community.roles.all()
        self.fields['committee'].queryset = community.committees.all()
