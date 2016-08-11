from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.formats import date_format
from django.utils.translation import ugettext_lazy as _
from ocd.base_models import UIDMixin, HTMLField, ConfidentialByRelationMixin
from ocd.base_managers import ConfidentialManager
from acl.default_roles import DefaultGroups


class AgendaItemManager(ConfidentialManager):
    """Manage queries over AgendaItem."""


@python_2_unicode_compatible
class AgendaItem(ConfidentialByRelationMixin):
    confidential_from = 'issue'
    objects = ConfidentialManager()
    meeting = models.ForeignKey('meetings.Meeting', on_delete=models.CASCADE, verbose_name=_("Meeting"), related_name="agenda")
    issue = models.ForeignKey('issues.Issue', on_delete=models.CASCADE, verbose_name=_("Issue"), related_name="agenda_items")
    background = HTMLField(_("Background"), null=True, blank=True)
    order = models.PositiveIntegerField(default=100, verbose_name=_("Order"))
    closed = models.BooleanField(_('Closed'), default=True)

    class Meta:
        unique_together = (("meeting", "issue"),)
        verbose_name = _("Agenda Item")
        verbose_name_plural = _("Agenda Items")
        ordering = ('meeting__created_at', 'order')

    def __str__(self):
        return self.issue.title

        # def natural_key(self):

    # return (self.meeting.natural_key(), self.issue.natural_key())
    # natural_key.dependencies = ['meetings.meeting', 'issues.issue']

    def attachments(self):
        return self.issue.attachments.filter(agenda_item=self)

    def comments(self):
        return self.issue.comments.filter(active=True, meeting=self.meeting)

    def proposals(self, user=None, committee=None):
        rv = self.issue.proposals.object_access_control(
            user=user, committee=committee).filter(
            active=True, decided_at_meeting=self.meeting)
        return rv

    def accepted_proposals(self, user=None, committee=None):
        from issues.models import ProposalStatus
        rv = self.proposals(user=user, committee=committee).filter(status=ProposalStatus.ACCEPTED)
        return rv

    def rejected_proposals(self, user=None, committee=None):
        from issues.models import ProposalStatus
        rv = self.proposals(user=user, committee=committee).filter(status=ProposalStatus.REJECTED)
        return rv


@python_2_unicode_compatible
class Meeting(UIDMixin):
    # community = models.ForeignKey('communities.Community', related_name="meetings", verbose_name=_("Community"))
    committee = models.ForeignKey('communities.Committee', on_delete=models.CASCADE, related_name="meetings", verbose_name=_("Committee"), null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="meetings_created",
                                   on_delete=models.CASCADE,
                                   verbose_name=_("Created by"))
    held_at = models.DateTimeField(_("Held at"))
    title = models.CharField(_("Title"), max_length=300, null=True, blank=True)
    scheduled_at = models.DateTimeField(_("Scheduled at"), null=True, blank=True)
    location = models.CharField(_("Location"), max_length=300, null=True, blank=True)
    comments = models.TextField(_("Comments"), null=True, blank=True)
    summary = models.TextField(_("Summary"), null=True, blank=True)
    agenda_items = models.ManyToManyField('issues.Issue', through=AgendaItem,
                                          blank=True,
                                          related_name='meetings',
                                          verbose_name=_("Agenda items"))
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          related_name="participated_in_meeting",
                                          verbose_name=_("Participants"),
                                          through='MeetingParticipant')
    guests = models.TextField(_("Guests"), null=True, blank=True, help_text=_("Enter each guest in a separate line"))

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ("-held_at", )

    def __str__(self):
        s = date_format(self.held_at)
        if self.title:
            s += " - " + self.title
        return s
        # return date_format(self.scheduled_at) + ", " + time_format(self.scheduled_at)

    # NEED TO FILTER THE QUERYSET AT RUNTIME FOR CONFIDENTIAL.
    # THIS METHOD IS NOT SAFE TO USE DIRECTLY ANYMORE
    # def get_active_issues(self):
    # return [ai.issue for ai in self.agenda.all() if ai.issue.active]

    def get_guest_list(self):
        if not self.guests:
            return []
        return filter(None, [s.strip() for s in self.guests.splitlines()])

    def get_title_or_date(self):
        return self.title or date_format(self.held_at)

    def get_title_or_shortdate(self):
        return self.title or self.held_at.strftime('%d/%m/%Y')

    def get_title_and_shortdate(self):
        if self.title:
            return self.held_at.strftime('%d/%m/%Y') + " - " + self.title
        else:
            return self.held_at.strftime('%d/%m/%Y')

    def get_participations(self):
        return self.participations.filter(is_absent=False)

    def get_participants(self):
        participations = self.get_participations()
        return [p.user for p in participations]

    def meeting_participants(self):
        meeting_participants = {'board': [], 'members': [], }
        board_ids = [m.user.id for m in self.committee.community.memberships.board()]
        for p in self.get_participations():
            if p.user.id in board_ids:
                meeting_participants['board'].append(p.user)
            else:
                meeting_participants['members'].append(p.user)

        # doing it simply like this, as I'd need to refactor models
        # just to order in the way that is now required.
        for index, item in enumerate(meeting_participants['board']):
            if item.get_default_group(self.committee.community) == DefaultGroups.CHAIRMAN:
                meeting_participants['board'].insert(0, meeting_participants['board'].pop(index))
        return meeting_participants

    @models.permalink
    def get_absolute_url(self):
        return "meeting", (self.committee.community.slug, self.committee.slug, str(self.pk))


class BoardParticipantsManager(models.Manager):
    def board(self):
        return self.get_queryset().exclude(default_group_name=DefaultGroups.MEMBER, is_absent=True)


@python_2_unicode_compatible
class MeetingParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=_("Meeting"), related_name="participations")
    ordinal = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="participations")
    # denormalize for history :
    display_name = models.CharField(_("Name"), max_length=200)
    default_group_name = models.CharField(_('Group'), max_length=50,
                                          choices=DefaultGroups.CHOICES,
                                          null=True, blank=True)
    is_absent = models.BooleanField(_("Is Absent"), default=False)
    objects = BoardParticipantsManager()

    class Meta:
        verbose_name = _("Meeting Participant")
        verbose_name_plural = _("Meeting Participants")
        unique_together = (('meeting', 'ordinal'), ('meeting', 'user'))

    def __str__(self):
        return self.user.display_name


# def natural_key(self):
# return (self.meeting.natural_key(), self.user.natural_key())
#     natural_key.dependencies = ['meetings.meeting', 'users.ocuser']


@python_2_unicode_compatible
class MeetingExternalParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, verbose_name=_("Meeting"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Meeting External Participant")
        verbose_name_plural = _("Meeting External Participants")

    def __str__(self):
        return self.name

#     def natural_key(self):
#         return (self.meetings.natural_key(), self.name)
#     natural_key.dependencies = ['meetings.meeting']
