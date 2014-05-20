from django.conf import settings
from django.db import models
from django.utils.formats import date_format
from django.utils.translation import ugettext_lazy as _
from issues.models import Issue, ProposalStatus
from ocd.base_models import UIDMixin, HTMLField
from users.default_roles import DefaultGroups


class AgendaItem(models.Model):
    meeting = models.ForeignKey('Meeting', verbose_name=_("Meeting"),
                                related_name="agenda")
    issue = models.ForeignKey(Issue, verbose_name=_("Issue"),
                              related_name="agenda_items")
    background = HTMLField(_("Background"), null=True, blank=True)
    order = models.PositiveIntegerField(default=100, verbose_name=_("Order"))
    closed = models.BooleanField(_('Closed'), default=True)

    class Meta:
        unique_together = (("meeting", "issue"),)
        verbose_name = _("Agenda Item")
        verbose_name_plural = _("Agenda Items")
        ordering = ('meeting__created_at', 'order')

    def __unicode__(self):
        return self.issue.title

#     def natural_key(self):
#         return (self.meeting.natural_key(), self.issue.natural_key())
#     natural_key.dependencies = ['meetings.meeting', 'issues.issue']

    def comments(self):
        return self.issue.comments.filter(active=True, meeting=self.meeting)

    @property
    def proposals(self):
        return self.issue.proposals.filter(active=True,
                                           decided_at_meeting=self.meeting)

    @property
    def accepted_proposals(self):
        return self.proposals.filter(status=ProposalStatus.ACCEPTED)

    @property
    def rejected_proposals(self):
        return self.proposals.filter(status=ProposalStatus.REJECTED)


class Meeting(UIDMixin):
    community = models.ForeignKey('communities.Community', related_name="meetings", verbose_name=_("Community"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="meetings_created", verbose_name=_("Created by"))

    held_at = models.DateTimeField(_("Held at"))

    title = models.CharField(_("Title"), max_length=300, null=True, blank=True)
    scheduled_at = models.DateTimeField(_("Scheduled at"),
                                        null=True, blank=True)
    location = models.CharField(_("Location"), max_length=300, null=True, blank=True)
    comments = models.TextField(_("Comments"), null=True, blank=True)

    summary = models.TextField(_("Summary"), null=True, blank=True)

    agenda_items = models.ManyToManyField(Issue, through=AgendaItem,
                                          blank=True,
                                          related_name='meetings',
                                          verbose_name=_("Agenda items"))

    participants = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          related_name="participated_in_meeting",
                                          verbose_name=_("Participants"),
                                          through='MeetingParticipant')

    guests = models.TextField(_("Guests"), null=True, blank=True,
                           help_text=_("Enter each guest in a separate line"))

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ("-held_at", )

    def __unicode__(self):
        s = date_format(self.held_at)
        if self.title:
            s += " - " + self.title
        return s
        #return date_format(self.scheduled_at) + ", " + time_format(self.scheduled_at)

    def get_active_issues(self):
        return [ai.issue for ai in self.agenda.all() if ai.issue.active]

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

        board_ids = [m.user.id for m in self.community.memberships.board()]

        for p in self.get_participations():
            if p.user.id in board_ids:
                meeting_participants['board'].append(p.user)
            else:
                meeting_participants['members'].append(p.user)

        # doing it simply like this, as I'd need to refactor models
        # just to order in the way that is now required.
        for index, item in enumerate(meeting_participants['board']):
            if item.get_default_group(self) == DefaultGroups.CHAIRMAN:
                meeting_participants['board'].insert(0,
                    meeting_participants['board'].pop(index))

        return meeting_participants

    @models.permalink
    def get_absolute_url(self):
        return ("meeting", (str(self.community.pk), str(self.pk),))


class BoardParticipantsManager(models.Manager):
    def board(self):
        return self.get_query_set().exclude(
                                    default_group_name=DefaultGroups.MEMBER,
                                    is_absent=True)

class MeetingParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, verbose_name=_("Meeting"),
                                related_name="participations")
    ordinal = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="participations")
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

    def __unicode__(self):
        return self.user

#     def natural_key(self):
#         return (self.meeting.natural_key(), self.user.natural_key())
#     natural_key.dependencies = ['meetings.meeting', 'users.ocuser']


class MeetingExternalParticipant(models.Model):
    meeting = models.ForeignKey(Meeting, verbose_name=_("Meeting"))
    name = models.CharField(max_length=200, verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Meeting External Participant")
        verbose_name_plural = _("Meeting External Participants")

    def __unicode__(self):
        return self.name

#     def natural_key(self):
#         return (self.meetings.natural_key(), self.name)
#     natural_key.dependencies = ['meetings.meeting']
