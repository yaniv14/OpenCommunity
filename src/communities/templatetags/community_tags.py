from django import template
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from users.models import Membership


register = template.Library()

@register.filter
def display_upcoming_time(community):
    """ display only date if hour information if not set (remains at default '00:00)
    """
    if not community.upcoming_meeting_scheduled_at:
        return _("--/--/--")
    when = timezone.localtime(community.upcoming_meeting_scheduled_at)
    t = when.timetz()
    if t.hour == 0 and t.minute == 0:
        return when.date()
    else:
        return when

        
@register.filter
def member_of(u, community):
    res = Membership.objects.filter(user=u)
    for membership in res:
        if membership.community == community:
            return True
    return False


@register.filter
def upcoming_status(community):
    from django.template.defaultfilters import date as _date
    
    rows = ['', '']
    if community.upcoming_meeting_started:
        rows[0] = _("Started")
    else:
        ver = _("Version")
        if community.upcoming_meeting_published_at:
            publish_time = timezone.localtime(
                    community.upcoming_meeting_published_at)
        else:
            publish_time = ''
            
        meeting_version = u'{0} {1} - {2}'.format(ver,
                            community.upcoming_meeting_version,
                            _date(publish_time, 'd F Y, H:i'))
        if community.upcoming_meeting_is_published:
            if community.straw_voting_enabled:
                if community.straw_vote_ended:
                    rows[0] = _("Straw vote ended")
                else:
                    rows[0] = _("Active straw vote")
                rows[1] = meeting_version
            else:
                rows[0] = _("Published")
                rows[1] = meeting_version
        else:
            rows[0] = _("Draft")

    return rows

@register.filter
def remove_email(args):
    return args.split('[')[0]
