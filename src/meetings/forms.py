from communities.models import SendToOption
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.html import mark_safe
from meetings.models import Meeting
from ocd.formfields import OCSplitDateTime
import floppyforms as forms


class CloseMeetingForm(forms.ModelForm):

    send_to_options = list(SendToOption.choices[2:])

    # On QA servers, allow users to prevent sending of protocols
    if settings.QA_SERVER:
        send_to_options.insert(0, SendToOption.choices[0])

    send_to = forms.TypedChoiceField(label=_("Send to"), coerce=int,
                                     choices=send_to_options,
                                     widget=forms.RadioSelect)
    issues = forms.MultipleChoiceField(label=_("The selected issues will be archived"), 
                                       choices=[],
                                       widget=forms.CheckboxSelectMultiple,
                                       required=False)

    class Meta:
        model = Meeting

        fields = (
                  'held_at',
                  )

        widgets = {
            'held_at': OCSplitDateTime,
        }

    def _get_issue_alert(self, issue):
        if not issue.changed_in_current():
            return _('Issue was not modified in this meeting')
        elif issue.open_proposals():
            return u'{0} {1}'.format(issue.open_proposals().count(),
                                    _('Undecided proposals'))
        else:
            return None


    def __init__(self, *args, **kwargs):
#         self.helper = FormHelper()
# 
#         self.helper.add_input(Submit('submit', _('Close Meeting')))
        issues = kwargs.pop('issues')
        super(CloseMeetingForm, self).__init__(*args, **kwargs)
        issues_op = []
        init_vals = []  # issues which 'archive' checkbox should be checked
        for issue in issues:
            choice_txt = issue.title
            alert_txt = self._get_issue_alert(issue)
            if alert_txt:
                choice_txt += u'<span class="help-text">{0}</span>'.format(alert_txt)
            else:
                # mark as ready for archive only when no alerts exist
                init_vals.append(issue.id) 
            issues_op.append((issue.id, mark_safe(choice_txt),))
        self.fields['issues'].choices = issues_op 
        self.fields['issues'].initial = init_vals
