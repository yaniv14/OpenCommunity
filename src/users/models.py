from __future__ import unicode_literals

from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from meetings.models import MeetingParticipant
from acl.default_roles import DefaultGroups
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


@python_2_unicode_compatible
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

    def __str__(self):
        return self.display_name

    def get_full_name(self):
        # The user is identified by their email address
        return self.display_name

    def get_short_name(self):
        # The user is identified by their email address
        return self.display_name

    def get_default_group(self, community):
        from users.models import CommunityMembership
        try:
            return self.memberships.get(community=community).default_group_name
        except CommunityMembership.DoesNotExist:
            return ""

    def get_related_groups(self, community):
        from users.models import CommunityMembership
        try:
            return [x.group_name_id for x in self.memberships.filter(community=community)]
        except CommunityMembership.DoesNotExist:
            return None

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])


# class MembershipManager(models.Manager):
#     def board(self):
#         return self.get_queryset().exclude(
#             default_group_name=DefaultGroups.MEMBER)
#
#     def none_board(self):
#         return self.get_queryset().filter(
#             default_group_name=DefaultGroups.MEMBER)


@python_2_unicode_compatible
class CommunityMembership(models.Model):
    community = models.ForeignKey('communities.Community', on_delete=models.CASCADE, verbose_name=_("Community"),
                                  related_name='community_memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"),
                             related_name='community_memberships')
    is_manager = models.BooleanField(verbose_name=_('Is community manager?'), default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   verbose_name=_("Invited by"),
                                   related_name="community_members_invited", null=True,
                                   blank=True)

    class Meta:
        unique_together = ("community", "user")
        verbose_name = _("Community Member")
        verbose_name_plural = _("Community Members")
        ordering = ['community']

    def __str__(self):
        return "%s: %s (%s)" % (self.community.name, self.user.display_name, self.is_manager)

    @models.permalink
    def get_absolute_url(self):
        return "member_profile", (self.community.slug, self.id)

    def get_committee_permissions(self, committee):
        committee_perms = self.get_permissions(committee.community)
        committee_perms.update(self.group_name.group_roles.get(committee=committee).role.all_perms())
        return committee_perms


@python_2_unicode_compatible
class CommitteeMembership(models.Model):
    committee = models.ForeignKey('communities.Committee', on_delete=models.CASCADE, verbose_name=_("Committee"),
                                  related_name='committee_memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"),
                             related_name='committee_memberships')
    role = models.ForeignKey('acl.Role', on_delete=models.CASCADE, verbose_name=_('Role'),
                             related_name='committee_memberships')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   verbose_name=_("Invited by"),
                                   related_name="committee_members_invited", null=True,
                                   blank=True)
    in_position_since = models.DateField(default=timezone.now, verbose_name=_("In position since"))

    # objects = CommitteeMembershipManager()

    class Meta:
        unique_together = ("committee", "user")
        verbose_name = _("Committee Member")
        verbose_name_plural = _("Committee Members")
        ordering = ['committee']

    def __str__(self):
        return "%s: %s (%s)" % (self.committee.name, self.user.display_name, self.role)

    @models.permalink
    def get_absolute_url(self):
        return "member_profile", (self.community.slug, self.id)

    def get_permissions(self, community):
        if self.group_name.title == 'administrator':
            return {'invite_member'}
        return set(community.roles.get(title='member').all_perms())

    def get_committee_group_permissions(self, committee):
        committee_perms = self.get_permissions(committee.community)
        committee_perms.update(self.group_name.group_roles.get(committee=committee).role.all_perms())
        return committee_perms

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

    def member_open_tasks(self, user=None, community=None):
        from issues.models import Proposal, ProposalStatus
        return Proposal.objects.object_access_control(
            user=user, community=community).filter(status=ProposalStatus.ACCEPTED, assigned_to_user=self.user,
                                                   active=True, task_completed=False).exclude(
            due_by__lte=datetime.date.today())

    def member_close_tasks(self, user=None, community=None):
        """ Need to create a field to determine closed tasks """
        from issues.models import Proposal, ProposalStatus
        return Proposal.objects.object_access_control(
            user=user, community=community).filter(status=ProposalStatus.ACCEPTED, assigned_to_user=self.user,
                                                   active=True, task_completed=True)

    def member_late_tasks(self, user=None, community=None):
        from issues.models import Proposal, ProposalStatus
        return Proposal.objects.object_access_control(
            user=user, community=community).filter(status=ProposalStatus.ACCEPTED, assigned_to_user=self.user,
                                                   due_by__lte=datetime.date.today(), active=True, task_completed=False)

    def member_votes_dict(self):
        from issues.models import ProposalVoteValue, ProposalStatus
        res = {'pro': {}, 'neut': {}, 'con': {}}
        pro_count = 0
        con_count = 0
        neut_count = 0
        votes = self.user.board_votes.select_related('proposal') \
            .filter(proposal__issue__community_id=self.community_id,
                    proposal__register_board_votes=True,
                    proposal__active=True,
                    proposal__decided_at_meeting__held_at__gte=self.in_position_since) \
            .exclude(proposal__status=ProposalStatus.IN_DISCUSSION).order_by('-proposal__issue__created_at',
                                                                             'proposal__id')
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
        from issues.models import ProposalVoteValue, ProposalStatus
        return self._user_board_votes().filter(value=ProposalVoteValue.PRO,
                                               proposal__status=ProposalStatus.ACCEPTED)

    def member_proposal_con_votes_rejected(self):
        from issues.models import ProposalVoteValue, ProposalStatus
        return self._user_board_votes().filter(value=ProposalVoteValue.CON,
                                               proposal__status=ProposalStatus.REJECTED)

    def member_proposal_nut_votes_accepted(self):
        from issues.models import ProposalVoteValue, ProposalStatus
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


@python_2_unicode_compatible
class Invitation(models.Model):
    community = models.ForeignKey('communities.Community',
                                  on_delete=models.CASCADE,
                                  verbose_name=_("Community"),
                                  related_name='invitations')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   verbose_name=_("Created by"),
                                   related_name="invitations_created")

    name = models.CharField(_("Name"), max_length=200, null=True, blank=True)
    email = models.EmailField(_("Email"))
    message = models.TextField(_("Message"), null=True, blank=True)

    code = models.CharField(max_length=CODE_LENGTH, default=create_code)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"), on_delete=models.CASCADE,
                             related_name='invitations', null=True, blank=True)

    groups = models.ManyToManyField('communities.CommunityGroup', verbose_name=_('Groups'),
                                    related_name='invitations')

    # TODO: Remove field.
    group_name = models.ForeignKey('communities.CommunityGroup', on_delete=models.CASCADE, verbose_name=_('Group'),
                                   related_name='g_invitations', null=True, blank=True)

    default_group_name = models.CharField(_('Group'), max_length=50,
                                          choices=DefaultGroups.CHOICES, blank=True, null=True)

    status = models.PositiveIntegerField(_("Status"),
                                         choices=EmailStatus.choices, default=EmailStatus.PENDING)
    times_sent = models.PositiveIntegerField(_("Times Sent"), default=0)
    error_count = models.PositiveIntegerField(_("Error count"), default=0)
    last_sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)

    class Meta:
        # unique_together = (("community", "email"),)

        verbose_name = _("Invitation")
        verbose_name_plural = _("Invitations")

    DEFAULT_MESSAGE = _("The system will allow you to take part in the decision making process of %s. "
                        "Once you've joined, you'll be able to see the topics for the agenda in the upcoming meeting, decisions at previous meetings, and in the near future you'll be able to discuss and influence them.")

    def __str__(self):
        return "%s: %s (%s)" % (self.community.name, self.email, self.group_name)

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
