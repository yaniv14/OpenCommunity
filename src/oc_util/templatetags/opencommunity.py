from __future__ import unicode_literals

import datetime

from django import template
from django.template import defaultfilters
from django.template.defaultfilters import stringfilter
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.utils.timezone import is_aware, utc
from django.utils.translation import pgettext, ungettext, ugettext as _, \
    ungettext, ugettext
from issues.models import ProposalVote, ProposalVoteBoard, ProposalVoteValue
register = template.Library()


@register.filter
@stringfilter
def userhtml(s):
    return mark_safe('<div class="userhtml">%s</div>' % s)


def simpletimesince(d, now=None, reversed=False):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n : ungettext('week', 'weeks', n)),
      (60 * 60 * 24, lambda n : ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n))
    )
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        now = datetime.datetime.now(utc if is_aware(d) else None)

    delta = (d - now) if reversed else (now - d)
    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return '0 ' + ugettext('minutes')
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = ugettext('%(number)d %(type)s') % {'number': count, 'type': name(count)}
#            s += ugettext(', %(number)d %(type)s') % {'number': count2, 'type': name2(count2)}
#        # Now get the second item
#        count2 = (since - (seconds * count)) // seconds2
#        if count2 != 0:
#        seconds2, name2 = chunks[i + 1]
#    if i + 1 < len(chunks):
    return s



# This filter doesn't require expects_localtime=True because it deals properly
# with both naive and aware datetimes. Therefore avoid the cost of conversion.
@register.filter
def octime(value):
    """
    For date and time values shows how many seconds, minutes, hours or days ago
    compared to current timestamp returns representing string.
    """
    if not isinstance(value, datetime.date): # datetime is a subclass of date
        return value

    now = datetime.datetime.now(utc if is_aware(value) else None)
    if value < now:
        delta = now - value
        if delta.days != 0:
            return pgettext(
                'naturaltime', '%(delta)s ago'
            ) % {'delta': simpletimesince(value, now)}
        elif delta.seconds == 0:
            return _('now')
        elif delta.seconds < 60:
            return ungettext(
                'a second ago', '%(count)s seconds ago', delta.seconds
            ) % {'count': delta.seconds}
        elif delta.seconds // 60 < 60:
            count = delta.seconds // 60
            return ungettext(
                'a minute ago', '%(count)s minutes ago', count
            ) % {'count': count}
        else:
            count = delta.seconds // 60 // 60
            return ungettext(
                'an hour ago', '%(count)s hours ago', count
            ) % {'count': count}
    else:
        delta = value - now
        if delta.days != 0:
            return pgettext(
                'naturaltime', '%(delta)s from now'
            ) % {'delta': defaultfilters.timeuntil(value, now)}
        elif delta.seconds == 0:
            return _('now')
        elif delta.seconds < 60:
            return ungettext(
                'a second from now', '%(count)s seconds from now', delta.seconds
            ) % {'count': delta.seconds}
        elif delta.seconds // 60 < 60:
            count = delta.seconds // 60
            return ungettext(
                'a minute from now', '%(count)s minutes from now', count
            ) % {'count': count}
        else:
            count = delta.seconds // 60 // 60
            return ungettext(
                'an hour from now', '%(count)s hours from now', count
            ) % {'count': count}

         
@register.filter
def ocshortdate(value):
    """
    For date and time values shows how many seconds, minutes, hours or days ago
    compared to current timestamp returns representing string.
    """
    if not isinstance(value, datetime.date): # datetime is a subclass of date
        return value

    now = datetime.date.today()
    if value.date() != now:
        return date_format(value, "DATE_FORMAT_OCSHORTDATE")
    return date_format(value, "DATE_FORMAT_OCSHORTTIME")


@register.filter
def minutes(value):
    if not isinstance(value, int):
        return value

    if not value:
        return None

    if value < 60:
        return "%d %s" % (value, _("minutes"))

    return "%d:%02d" % (value / 60, value % 60)


@register.filter
def minutes_strict(value):
    if value is None:
        return "00:00"

    if not isinstance(value, int): 
        return value

    return "%02d:%02d" % (value / 60, value % 60) if value else "?"


    return [v.user for v in res]

"""
def board_vote(proposal, val, participants):
    voter_ids = ProposalVoteBoard.objects.filter(proposal=proposal) \
                .values_list('user', flat=True)
    non_voters = [u for u in participants.all() if u.id not in voter_ids]
    res = ProposalVoteBoard.objects.filter(proposal=proposal) \
                                      .values_list('id', flat=True))
    return [v.user for v in res]
"""

def board_voters_on_proposal(proposal):
    """ potential board voters """
    if proposal.decided_at_meeting:
        board_attn = proposal.decided_at_meeting.participations.board() 
    else:
        c = proposal.issue.community
        board_attn = c.memberships.board().filter(
                    user__in=c.upcoming_meeting_participants.all())
        
    participants = [b.user for b in board_attn]
    return participants 


@register.filter
def board_votes_count(p):
    return len(board_voters_on_proposal(p))


@register.filter
def board_by_vote(p, val):
    participants = board_voters_on_proposal(p)
    if val == 'neut':
        """
        voter_ids = ProposalVoteBoard.objects.filter(proposal=p) \
                    .exclude(value=ProposalVoteValue.NEUTRAL) \
                    .values_list('user', flat=True)
        return [u for u in participants if u.id not in voter_ids]
        """
        vote = ProposalVoteValue.NEUTRAL
    elif val == 'pro':
        vote = ProposalVoteValue.PRO
    elif val == 'con':
        vote = ProposalVoteValue.CON
    res = ProposalVoteBoard.objects.filter(proposal=p, value=vote, 
                            user__in=participants)
    
    return [v.user for v in res]

"""
@register.simple_tag
def board_votes_in_meeting(proposal, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id)
"""
