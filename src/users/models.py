from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, \
    PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from issues.models import Proposal, ProposalVote, ProposalVoteValue, \
    ProposalStatus
from meetings.models import MeetingParticipant
from users.default_roles import DefaultGroups
import datetime
import logging
import random
import string

CODE_LENGTH = 48

logger = logging.getLogger(__name__)


class OCUserManager(BaseUserManager):

    @classmethod
    def normalize_email(cls, email):
        return email.lower()

    def get_by_natural_key(self, username):
        return self.get(email__iexact=username)

    def create_user(self, email, display_name=None, password=None, **kwargs):
        """
        Creates and saves a User with the given email, display name and
        password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        if not display_name:
            display_name = email

        user = self.model(
            email=OCUserManager.normalize_email(email),
            display_name=display_name,
            **kwargs
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, display_name, password):
        """
        Creates and saves a superuser with the given email, display name and
        password.
        """
        user = self.create_user(email,
            password=password,
            display_name=display_name
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class OCUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), max_length=255, unique=True,
        db_index=True,
    )
    display_name = models.CharField(_("Your name"), max_length=200)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
           help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = OCUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return self.display_name

    def get_full_name(self):
        # The user is identified by their email address
        return self.display_name

    def get_short_name(self):
        # The user is identified by their email address
        return self.display_name

    def get_default_group(self, community):
        try:
            return self.memberships.get(community=community).default_group_name
        except Membership.DoesNotExist:
            return ""

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


class MembershipManager(models.Manager):
    def board(self):
        return self.get_query_set().exclude(
                                    default_group_name=DefaultGroups.MEMBER)

    def none_board(self):
        return self.get_query_set().filter(
                                    default_group_name=DefaultGroups.MEMBER)


class Membership(models.Model):
    community = models.ForeignKey('communities.Community', verbose_name=_("Community"),
                                  related_name='memberships')
    user = models.ForeignKey(OCUser, verbose_name=_("User"),
                             related_name='memberships')
    default_group_name = models.CharField(_('Group'), max_length=50,
                                          choices=DefaultGroups.CHOICES)

    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_("Created at"))
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   verbose_name=_("Invited by"),
                                   related_name="members_invited", null=True,
                                   blank=True)
    in_position_since = models.DateField(default=datetime.date.today(),
                                         verbose_name=_("In position since"))
    objects = MembershipManager()

    class Meta:
        unique_together = (("community", "user"),)
        verbose_name = _("Community Member")
        verbose_name_plural = _("Community Members")

    def __unicode__(self):
        return "%s: %s (%s)" % (self.community.name, self.user.display_name,
                                self.get_default_group_name_display())

    @models.permalink
    def get_absolute_url(self):
        return "member_profile", (self.community.id, self.id)

    def get_permissions(self):
        return DefaultGroups.permissions[self.default_group_name]
    
    def total_meetings(self):
        """ In the future we'll check since joined to community or rejoined """
        return self.community.meetings.filter(held_at__gte=self.in_position_since).count()
        
    def meetings_participation(self):
        """ In the future we'll check since joined to community or rejoined """
        return MeetingParticipant.objects.filter(user=self.user, is_absent=False,
                                                 meeting__community=self.community,
                                                 meeting__held_at__gte=self.in_position_since).count()
    
    def meetings_participation_percantage(self):
        """ In the future we'll check since joined to community or rejoined """
        return round((float(self.meetings_participation()) / float(self.total_meetings())) * 100.0)

    def member_open_tasks(self):
        return Proposal.objects.filter(status=ProposalStatus.ACCEPTED, assigned_to_user=self.user, active=True, task_completed=False).exclude(due_by__lte=datetime.date.today())

    def member_close_tasks(self):
        """ Need to create a field to determine closed tasks """
        return Proposal.objects.filter(status=ProposalStatus.ACCEPTED, assigned_to_user=self.user, active=True, task_completed=True)

    def member_late_tasks(self):
        return Proposal.objects.filter(status=ProposalStatus.ACCEPTED, assigned_to_user=self.user, due_by__lte=datetime.date.today(), active=True, task_completed=False)

    def member_votes_dict(self):
        res = {'pro': {}, 'neut': {}, 'con': {}}
        pro_count = 0
        con_count = 0
        neut_count = 0
        votes = self.user.board_votes.select_related('proposal') \
              .filter(proposal__issue__community_id=self.community_id,
                      proposal__register_board_votes=True,
                      proposal__active=True,
                      proposal__decided_at_meeting__held_at__gte=self.in_position_since) \
              .exclude(proposal__status=ProposalStatus.IN_DISCUSSION).order_by('-proposal__issue__created_at', 'proposal__id')
        for v in votes:
            if not v.proposal.register_board_votes:
                continue
            if v.value == ProposalVoteValue.NEUTRAL:
                key = 'neut'
                neut_count += 1
            elif v.value == ProposalVoteValue.PRO:
                key = 'pro'
                pro_count += 1
            elif v.value == ProposalVoteValue.CON:
                key = 'con'
                con_count += 1
            issue_key = v.proposal.issue
            p_list = res[key].setdefault(issue_key, [])
            p_list.append(v.proposal)
        res['pro_count'] = pro_count
        res['con_count'] = con_count
        res['neut_count'] = neut_count
        return res

    def _user_board_votes(self):
        return self.user.board_votes.select_related('proposal').filter(proposal__issue__community_id=self.community_id, 
                      proposal__active=True,
                      proposal__register_board_votes=True,
                      proposal__decided_at_meeting__held_at__gte=self.in_position_since) 

    def member_proposal_pro_votes_accepted(self):
        return self._user_board_votes().filter(value=ProposalVoteValue.PRO, 
                                              proposal__status=ProposalStatus.ACCEPTED)
    def member_proposal_con_votes_rejected(self):
        return self._user_board_votes().filter(value=ProposalVoteValue.CON,
                                              proposal__status=ProposalStatus.REJECTED)

    def member_proposal_nut_votes_accepted(self):
        return self._user_board_votes().filter(value=ProposalVoteValue.NEUTRAL,
                                              proposal__status=ProposalStatus.ACCEPTED)

CODE_CHARS = string.lowercase + string.digits


def create_code(length=CODE_LENGTH):
    """
    Creates a random code of lowercase letters and numbers
    """
    return "".join(random.choice(CODE_CHARS) for _x in xrange(length))


class EmailStatus(object):
    PENDING = 0
    SENT = 1
    FAILED = 2

    choices = (
               (PENDING, _('Pending')),
               (SENT, _('Sent')),
               (FAILED, _('Failed')),
               )


class Invitation(models.Model):
    community = models.ForeignKey('communities.Community',
                                  verbose_name=_("Community"),
                                  related_name='invitations')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   verbose_name=_("Created by"),
                                   related_name="invitations_created")

    name = models.CharField(_("Name"), max_length=200, null=True, blank=True)
    email = models.EmailField(_("Email"))
    message = models.TextField(_("Message"), null=True, blank=True)

    code = models.CharField(max_length=CODE_LENGTH, default=create_code)

    user = models.ForeignKey(OCUser, verbose_name=_("User"),
                             related_name='invitations', null=True, blank=True)

    default_group_name = models.CharField(_('Group'), max_length=50,
                                          choices=DefaultGroups.CHOICES)

    status = models.PositiveIntegerField(_("Status"),
                     choices=EmailStatus.choices, default=EmailStatus.PENDING)
    times_sent = models.PositiveIntegerField(_("Times Sent"), default=0)
    error_count = models.PositiveIntegerField(_("Error count"), default=0)
    last_sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)

    class Meta:
        unique_together = (("community", "email"),)

        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")

    DEFAULT_MESSAGE = _("The system will allow you to take part in the decision making process of %s. "
                        "Once you've joined, you'll be able to see the topics for the agenda in the upcoming meeting, decisions at previous meetings, and in the near future you'll be able to discuss and influence them.")

    def __unicode__(self):
        return "%s: %s (%s)" % (self.community.name, self.email,
                                self.get_default_group_name_display())

    @models.permalink
    def get_absolute_url(self):
        return "accept_invitation", (self.code,)


    def send(self, sender, recipient_name='', base_url=None):

        if not base_url:
            base_url = settings.HOST_URL

        subject = _("Invitation to %s") % self.community.name
        d = {
              'base_url': base_url,
              'object': self,
              'recipient_name': recipient_name,
             }

        message = render_to_string("emails/invitation.txt", d)
        recipient_list = [self.email]
        from_email = "%s <%s>" % (self.community.name, settings.FROM_EMAIL)
        self.last_sent_at = timezone.now()

        try:
            send_mail(subject, message, from_email, recipient_list)
            self.times_sent += 1
            self.status = EmailStatus.SENT
            self.save()
            return True
        except:
            logger.error("Invitation email sending failed", exc_info=True)
            self.error_count += 1
            self.status = EmailStatus.FAILED
            self.save()
            return False
