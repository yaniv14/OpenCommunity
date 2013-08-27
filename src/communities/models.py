from django.conf import settings
from django.db import models
from django.db.models.query_utils import Q
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from ocd.email import send_mails
from users.default_roles import DefaultGroups
from users.models import OCUser
import logging
from ocd.base_models import HTMLField, UIDMixin


logger = logging.getLogger(__name__)


class SendToOption(object):

    ONLY_ME = 1
    ONLY_ATTENDEES = 2
    BOARD_ONLY = 3
    ALL_MEMBERS = 4

    choices = (
               (ONLY_ME, _("Only Me (review)")),
               (ONLY_ATTENDEES, _("Only attendees")),
               (BOARD_ONLY, _("The Board")),
               (ALL_MEMBERS, _("All Members")),
              )

    publish_choices = (
               (ONLY_ME, _("Only Me (review)")),
               (BOARD_ONLY, _("The Board")),
               (ALL_MEMBERS, _("All Members")),
              )


class Community(UIDMixin):

    name = models.CharField(max_length=200, verbose_name=_("Name"))
    is_public = models.BooleanField(_("Public Community"), default=False,
                                    db_index=True)
    logo = models.ImageField(upload_to='community_logo', verbose_name=_("Community Logo"), blank=True, null=True)
    official_identifier = models.CharField(max_length=300, verbose_name=_("Community Identifier"), blank=True, null=True)

    upcoming_meeting_started = models.BooleanField(
                                        _("Meeting started"),
                                        default=False)
    upcoming_meeting_title = models.CharField(
                                         _("Upcoming meeting title"),
                                         max_length=300, null=True,
                                         blank=True)
    upcoming_meeting_scheduled_at = models.DateTimeField(
                                        _("Upcoming meeting scheduled at"),
                                        blank=True, null=True)
    upcoming_meeting_location = models.CharField(
                                         _("Upcoming meeting location"),
                                         max_length=300, null=True,
                                         blank=True)
    upcoming_meeting_comments = HTMLField(_("Upcoming meeting background"),
                                          null=True, blank=True)

    upcoming_meeting_participants = models.ManyToManyField(
                                      settings.AUTH_USER_MODEL,
                                      blank=True,
                                      related_name="+",
                                      verbose_name=_(
                                         "Participants in upcoming meeting"))

    upcoming_meeting_guests = models.TextField(_("Guests in upcoming meeting"),
                           null=True, blank=True,
                           help_text=_("Enter each guest in a separate line"))

    upcoming_meeting_version = models.IntegerField(
                                   _("Upcoming meeting version"), default=0)

    upcoming_meeting_is_published = models.BooleanField(
                                        _("Upcoming meeting is published"),
                                        default=False)
    upcoming_meeting_published_at = models.DateTimeField(
                                        _("Upcoming meeting published at"),
                                        blank=True, null=True)

    upcoming_meeting_summary = HTMLField(_("Upcoming meeting summary"),
                                         null=True, blank=True)
    board_name = models.CharField(_("Board Name"), max_length=200,
                                  null=True, blank=True)

    class Meta:
        verbose_name = _("Community")
        verbose_name_plural = _("Communities")

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return "community", (str(self.pk),)

    @models.permalink
    def get_upcoming_absolute_url(self):
        return "community", (str(self.pk),)

    def upcoming_issues(self, upcoming=True):
        return self.issues.filter(active=True, is_closed=False,
            in_upcoming_meeting=upcoming).order_by('order_in_upcoming_meeting')

    def available_issues(self):
        return self.upcoming_issues(False)

    def issues_ready_to_close(self):
        return self.upcoming_issues().filter(
                                         proposals__is_accepted=True
                                     ).annotate(
                                        num_proposals=models.Count('proposals')
                                     )

    def get_board_name(self):
        return self.board_name or _('Board')

    def get_members(self):
        return OCUser.objects.filter(memberships__community=self)

    def get_guest_list(self):
        if not self.upcoming_meeting_guests:
            return []
        return filter(None, [s.strip() for s in self.upcoming_meeting_guests.splitlines()])

    def send_mail(self, template, sender, send_to, data=None, base_url=None):

        if not base_url:
            base_url = settings.HOST_URL

        d = data.copy() if data else {}

        d.update({
              'base_url': base_url,
              'community': self,
              'LANGUAGE_CODE': settings.LANGUAGE_CODE,
             })

        subject = render_to_string("emails/%s_title.txt" % template, d).strip()

        message = render_to_string("emails/%s.txt" % template, d)
        html_message = render_to_string("emails/%s.html" % template, d)
        from_email = "%s <%s>" % (self.name, settings.FROM_EMAIL)

        recipient_list = set([sender.email])

        if send_to == SendToOption.ALL_MEMBERS:
            recipient_list.update(list(
                      self.memberships.values_list('user__email', flat=True)))
        elif send_to == SendToOption.BOARD_ONLY:
            recipient_list.update(list(
                        self.memberships.board().values_list('user__email', flat=True)))
        elif send_to == SendToOption.ONLY_ATTENDEES:
            recipient_list.update(list(
                       self.upcoming_meeting_participants.values_list(
                                                          'email', flat=True)))

        logger.info("Sending agenda to %d users" % len(recipient_list))

        send_mails(from_email, recipient_list, subject, message, html_message)

        return len(recipient_list)
