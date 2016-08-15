from __future__ import unicode_literals
from django.conf import settings
from django.db import models, transaction
from django.db.models.signals import post_save
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext, ugettext_lazy as _
from ocd.base_models import HTMLField, UIDMixin, UIDManager, ConfidentialMixin
from ocd.base_managers import ConfidentialQuerySetMixin, ActiveQuerySetMixin
from ocd.storages import uploads_storage
from ocd.validation import enhance_html
from taggit.managers import TaggableManager
import meetings
import os.path
from itertools import groupby


class IssueManager(ConfidentialQuerySetMixin, ActiveQuerySetMixin, UIDManager):
    pass


class ProposalQuerySetMixin(ActiveQuerySetMixin):
    """Exposes methods that can be used on both the manager and the queryset.

    This allows us to chain custom methods.

    """

    def open(self):
        return self.filter(active=True, decided_at_meeting_id=None).order_by("created_at")

    def closed(self):
        return self.filter(active=True).exclude(decided_at_meeting_id=None)


class ProposalQuerySet(QuerySet, ProposalQuerySetMixin):
    """Queryset used by the Porposal Manager."""


class ProposalManager(models.Manager, ConfidentialQuerySetMixin, ProposalQuerySetMixin):
    def get_queryset(self):
        return ProposalQuerySet(self.model, using=self._db)


class IssueStatus(object):
    OPEN = 1
    IN_UPCOMING_MEETING = 2
    IN_UPCOMING_MEETING_COMPLETED = 3  # TODO: remove me safely
    ARCHIVED = 4

    choices = (
        (OPEN, _('Open')),
        (IN_UPCOMING_MEETING, _('In upcoming meeting')),
        (IN_UPCOMING_MEETING_COMPLETED, _('In upcoming meeting (completed)')),
        (ARCHIVED, _('Archived')),
    )

    IS_UPCOMING = (IN_UPCOMING_MEETING, IN_UPCOMING_MEETING_COMPLETED)
    NOT_IS_UPCOMING = (OPEN, ARCHIVED)


@python_2_unicode_compatible
class Issue(UIDMixin, ConfidentialMixin):
    objects = IssueManager()
    active = models.BooleanField(_("Active"), default=True)
    committee = models.ForeignKey('communities.Committee', on_delete=models.CASCADE, related_name="issues", null=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Created by"),
                                   related_name="issues_created")
    title = models.CharField(_("Title"), max_length=300)
    abstract = HTMLField(_("Background"), null=True, blank=True)
    content = HTMLField(_("Content"), null=True, blank=True)  # TODO: remove me safely
    calculated_score = models.IntegerField(_("Calculated Score"), default=0)  # TODO: remove me
    status = models.IntegerField(choices=IssueStatus.choices, default=IssueStatus.OPEN)
    statuses = IssueStatus
    order_in_upcoming_meeting = models.IntegerField(_("Order in upcoming meeting"), default=0, null=True, blank=True)
    order_by_votes = models.FloatField(_("Order in upcoming meeting by votes"), default=0, null=True, blank=True)
    length_in_minutes = models.IntegerField(_("Length (in minutes)"), null=True, blank=True)
    completed = models.BooleanField(_("Discussion completed"), default=False)  # TODO: remove me safely
    is_published = models.BooleanField(_("Is published to members"), default=False)

    class Meta:
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")
        ordering = ['order_in_upcoming_meeting', 'title']

    def __str__(self):
        return self.title

    @models.permalink
    def get_edit_url(self):
        return "issue_edit", (self.committee.community.slug, self.committee.slug, str(self.pk))

    @models.permalink
    def get_delete_url(self):
        return "issue_delete", (self.committee.community.slug, self.committee.slug, str(self.pk))

    @models.permalink
    def get_absolute_url(self):
        return "issue", (self.committee.community.slug, self.committee.slug, str(self.pk))

    @models.permalink
    def get_next_upcoming_issue_url(self):
        try:
            next = Issue.objects.filter(committee=self.committee, status=2).filter(
                order_in_upcoming_meeting__gt=self.order_in_upcoming_meeting).order_by('order_in_upcoming_meeting')[0]
            return "issue", (self.committee.community.slug, self.committee.slug, str(next.pk))
        except:
            return "committee", (self.committee.community.slug, self.committee.slug)

    def active_proposals(self):
        return self.proposals.filter(active=True)

    def open_proposals(self):
        return self.active_proposals().filter(
            status=Proposal.statuses.IN_DISCUSSION)

    def active_comments(self):
        return self.comments.filter(active=True)

    def new_comments(self):
        return self.comments.filter(meeting_id=None)

    def historical_comments(self):
        return self.comments.filter(active=True).exclude(meeting_id=None)

    def has_closed_parts(self):
        """ Should be able to be viewed """

    @property
    def is_upcoming(self):
        return self.status in IssueStatus.IS_UPCOMING

    @property
    def is_current(self):
        return self.status in IssueStatus.IS_UPCOMING and self.committee.upcoming_meeting_started

    def changed_in_current(self):
        decided_at_current = self.proposals.filter(active=True,
                                                   decided_at_meeting=None,
                                                   status__in=[
                                                       ProposalStatus.ACCEPTED,
                                                       ProposalStatus.REJECTED
                                                   ])
        return decided_at_current or self.new_comments().filter(active=True)

    @property
    def is_archived(self):
        return self.status == IssueStatus.ARCHIVED

    @property
    def in_closed_meeting(self):
        return meetings.models.AgendaItem.objects.filter(issue=self).exists()

    @property
    def can_straw_vote(self):

        # test date/time limit
        if self.committee.voting_ends_at:
            time_till_close = self.committee.voting_ends_at - timezone.now()
            if time_till_close.total_seconds() <= 0:
                return False

        return self.committee.straw_voting_enabled and \
               self.is_upcoming and \
               self.committee.upcoming_meeting_is_published and \
               self.proposals.open().count() > 0

    def current_attachments(self):
        """Returns attachments not yet attached to an agenda item"""
        return self.attachments.filter(agenda_item__isnull=True)


class IssueComment(UIDMixin):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="comments")
    active = models.BooleanField(default=True)
    ordinal = models.PositiveIntegerField(null=True, blank=True)  # TODO: remove me
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Created by"),
                                   related_name="issue_comments_created")
    meeting = models.ForeignKey('meetings.Meeting', on_delete=models.CASCADE, null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    last_edited_at = models.DateTimeField(_("Last Edited at"), auto_now_add=True)
    last_edited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Created by"),
                                       related_name="issue_comments_last_edited", null=True, blank=True)
    content = HTMLField(_("Comment"))

    @property
    def is_confidential(self):
        return self.issue.is_confidential

    class Meta:
        ordering = ('created_at',)
        verbose_name = _("Issue comment")
        verbose_name_plural = _("Issue comments")

    @property
    def is_open(self):
        return self.meeting_id is None

    def update_content(self, expected_version, author, content):
        """ creates a new revision and updates current comment """
        if self.version != expected_version:
            return False

        content = enhance_html(content.strip())

        if self.content == content:
            return True

        with transaction.atomic():
            IssueCommentRevision.objects.create(comment=self,
                                                version=expected_version,
                                                created_at=self.created_at,
                                                created_by=self.created_by,
                                                content=self.content)
            self.version += 1
            self.last_edited_at = timezone.now()
            self.last_edited_by = author
            self.content = content
            self.save()

        return True

    @models.permalink
    def get_delete_url(self):
        return "delete_issue_comment", (self.issue.committee.community.slug, self.issue.committee.slug, self.id)

    @models.permalink
    def get_edit_url(self):
        return "edit_issue_comment", (self.issue.committee.community.slug, self.issue.committee.slug, self.id)

    @models.permalink
    def get_absolute_url(self):
        return "issue", (self.issue.committee.community.slug, self.issue.committee.slug, str(self.issue.pk))


class IssueCommentRevision(models.Model):
    """ Holds data for historical comments """
    comment = models.ForeignKey(IssueComment, on_delete=models.CASCADE, related_name='revisions')
    version = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   verbose_name=_("Created by"),
                                   related_name="issue_comment_versions_created")
    content = models.TextField(verbose_name=_("Content"))

    @property
    def is_confidential(self):
        return self.comment.issue.is_confidential


def issue_attachment_path(instance, filename):
    filename = get_valid_filename(os.path.basename(filename))
    return os.path.join(instance.issue.committee.uid, instance.issue.uid,
                        filename)


class IssueAttachment(UIDMixin):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="attachments")
    agenda_item = models.ForeignKey('meetings.AgendaItem', on_delete=models.CASCADE, null=True, blank=True, related_name="attachments")
    file = models.FileField(_("File"), storage=uploads_storage, max_length=200, upload_to=issue_attachment_path)
    title = models.CharField(_("Title"), max_length=100)
    active = models.BooleanField(default=True)
    ordinal = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(_("File created at"), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Created by"), related_name="files_created")

    @property
    def is_confidential(self):
        return self.issue.is_confidential

    def get_icon(self):
        # TODO: move to settings
        file_icon_map = {
            'doc': 'doc',
            'docx': 'doc',
            'rtf': 'doc',
            'jpg': 'img',
            'jpeg': 'img',
            'gif': 'img',
            'png': 'img',
            'tiff': 'img',
            'xls': 'xl',
            'xlsx': 'xl',
            'csv': 'xl',
            'pdf': 'pdf',
            'ppt': 'ppt',
            'pptx': 'ppt',
            'm4a': 'vid',
            'wma': 'vid',
            'mp4': 'vid',
            'mov': 'vid',
            'avi': 'vid',
            'wmv': 'vid',
            'aac': 'snd',
            'fla': 'snd',
            'wav': 'snd',
            'mp3': 'snd',
            'flac': 'snd',
            'txt': 'txt',
        }
        ext = os.path.splitext(self.file.name)[1][1:] or ''
        try:
            icon = file_icon_map[ext.lower()]
        except KeyError:
            icon = 'file'
        return icon

    class Meta:
        ordering = ('created_at',)

    @models.permalink
    def get_absolute_url(self):
        return "attachment_download", (
            self.issue.committee.community.slug,
            self.issue.committee.slug,
            str(self.issue.pk),
            str(self.pk)
        )


class ProposalVoteValue(object):
    CON = -1
    NEUTRAL = 0
    PRO = 1

    CHOICES = (
        (CON, ugettext("Con")),
        (NEUTRAL, ugettext("Neutral")),
        (PRO, ugettext("Pro")),
    )


class ProposalVoteArgumentVoteValue(object):
    CON = -1
    PRO = 1

    CHOICES = (
        (CON, ugettext("Con")),
        (PRO, ugettext("Pro")),
    )


@python_2_unicode_compatible
class ProposalVoteBoard(models.Model):
    proposal = models.ForeignKey("Proposal", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"), related_name="board_votes")
    value = models.SmallIntegerField(_("Vote"), choices=ProposalVoteValue.CHOICES, default=ProposalVoteValue.NEUTRAL)
    voted_by_chairman = models.BooleanField(_("Voted by chairman"), default=False)  # TODO: by who?

    @property
    def is_confidential(self):
        return self.proposal.is_confidential

    class Meta:
        unique_together = (("proposal", "user"),)
        verbose_name = _("Proposal Vote")
        verbose_name_plural = _("Proposal Votes")

    def __str__(self):
        return "%s - %s" % (self.proposal.issue.title, self.user.display_name)


class ProposalType(object):
    TASK = 1
    RULE = 2
    ADMIN = 3

    CHOICES = (
        (TASK, ugettext("Task")),
        (RULE, ugettext("Rule")),
        (ADMIN, ugettext("General")),
    )


class ProposalStatus(object):
    IN_DISCUSSION = 1
    ACCEPTED = 2
    REJECTED = 3

    choices = (
        (IN_DISCUSSION, _('In discussion')),
        (ACCEPTED, _('Accepted')),
        (REJECTED, _('Rejected')),
    )


@python_2_unicode_compatible
class Proposal(UIDMixin, ConfidentialMixin):
    objects = ProposalManager()
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name="proposals")
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Create at"), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name="proposals_created",
                                   verbose_name=_("Created by"))
    type = models.PositiveIntegerField(_("Type"), choices=ProposalType.CHOICES)
    types = ProposalType
    title = models.CharField(_("Title"), max_length=300)
    content = HTMLField(_("Details"), null=True, blank=True)
    status = models.IntegerField(choices=ProposalStatus.choices, default=ProposalStatus.IN_DISCUSSION)
    statuses = ProposalStatus
    decided_at_meeting = models.ForeignKey('meetings.Meeting', on_delete=models.CASCADE, null=True, blank=True)
    assigned_to = models.CharField(_("Assigned to"), max_length=200, null=True, blank=True)
    assigned_to_user = models.ForeignKey(settings.AUTH_USER_MODEL,
                                         on_delete=models.CASCADE,
                                         verbose_name=_("Assigned to user"),
                                         null=True, blank=True,
                                         related_name="proposals_assigned")
    due_by = models.DateField(_("Due by"), null=True, blank=True)
    task_completed = models.BooleanField(_("Completed"), default=False)
    votes_pro = models.PositiveIntegerField(_("Votes pro"), null=True, blank=True)
    votes_con = models.PositiveIntegerField(_("Votes con"), null=True, blank=True)
    community_members = models.PositiveIntegerField(_("Community members"), null=True, blank=True)
    tags = TaggableManager(_("Tags"), blank=True)
    register_board_votes = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Proposal")
        verbose_name_plural = _("Proposals")

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.decided_at_meeting is None

    @property
    def decided(self):
        return self.status != ProposalStatus.IN_DISCUSSION

    @property
    def can_vote(self):
        """ Returns True if the proposal, issue and meeting are open """
        return self.is_open and self.issue.is_current

    @property
    def has_votes(self):
        """ Returns True if the proposal has any vote """
        return self.votes_con or self.votes_pro

    @property
    def has_arguments(self):
        return ProposalVoteArgument.objects.filter(proposal_vote__proposal=self).exists()

    @property
    def can_straw_vote(self):
        return self.status == ProposalStatus.IN_DISCUSSION and self.issue.can_straw_vote

    @property
    def can_show_straw_votes(self):
        return self.has_votes and \
               (not self.issue.is_upcoming or \
                not self.issue.committee.upcoming_meeting_is_published or \
                self.issue.committee.straw_vote_ended)

    def get_straw_results(self, meeting_id=None):
        """ get straw voting results registered for the given meeting """
        if meeting_id:
            try:
                res = VoteResult.objects.get(proposal=self, meeting_id=meeting_id)
            except VoteResult.DoesNotExist:
                return None
            return res
        else:
            if self.issue.is_upcoming and self.issue.committee.straw_vote_ended:
                return self
            else:
                try:
                    res = VoteResult.objects.filter(proposal=self).latest('meeting__held_at')
                    return res
                except VoteResult.DoesNotExist:
                    return None

    def board_vote_by_member(self, user_id):
        try:
            vote = ProposalVoteBoard.objects.get(user_id=user_id, proposal=self)
            return vote.value
        except ProposalVoteBoard.DoesNotExist:
            return None

    @property
    def board_vote_result(self):
        total_votes = 0
        votes_dict = {'sums': {}, 'total': total_votes, 'per_user': {}}
        pro_count = 0
        con_count = 0
        neut_count = 0

        users = self.issue.committee.upcoming_meeting_participants.all()
        for u in users:
            vote = ProposalVoteBoard.objects.filter(proposal=self, user=u)
            if vote.exists():
                votes_dict['per_user'][u] = vote[0].value
                if vote[0].value == 1:
                    pro_count += 1
                    total_votes += 1
                elif vote[0].value == -1:
                    con_count += 1
                    total_votes += 1
                elif vote[0].value == 0:
                    neut_count += 1

            else:
                votes_dict['per_user'][u] = 0
                neut_count += 1

        votes_dict['sums']['pro_count'] = pro_count
        votes_dict['sums']['con_count'] = con_count
        votes_dict['sums']['neut_count'] = neut_count
        votes_dict['total'] = total_votes
        return votes_dict

    def do_votes_summation(self, members_count):

        pro_votes = ProposalVote.objects.filter(proposal=self, value=ProposalVoteValue.PRO).count()
        con_votes = ProposalVote.objects.filter(proposal=self, value=ProposalVoteValue.CON).count()
        self.votes_pro = pro_votes
        self.votes_con = con_votes
        self.community_members = members_count
        self.save()

    def is_task(self):
        return self.type == ProposalType.TASK

    @models.permalink
    def get_absolute_url(self):
        return "proposal", (
            self.issue.committee.community.slug, self.issue.committee.slug, str(self.issue.pk), str(self.pk))

    @models.permalink
    def get_email_vote_url(self):
        return "vote_on_proposal", (self.issue.committee.community.slug, self.issue.committee.slug, str(self.pk))

    @models.permalink
    def get_edit_url(self):
        return (
            "proposal_edit",
            (self.issue.committee.community.slug, self.issue.committee.slug, str(self.issue.pk), str(self.pk)))

    @models.permalink
    def get_edit_task_url(self):
        return ("proposal_edit_task",
                (self.issue.committee.community.slug, self.issue.committee.slug, str(self.issue.pk), str(self.pk)))

    @models.permalink
    def get_delete_url(self):
        return (
            "proposal_delete",
            (self.issue.committee.community.slug, self.issue.committee.slug, str(self.issue.pk),
             str(self.pk)))

    def get_status_class(self):
        if self.status == self.statuses.ACCEPTED:
            return "accepted"
        if self.status == self.statuses.REJECTED:
            return "rejected"
        return ""

    def enforce_confidential_rules(self):
        # override `enforce_confidential_rules` on ConfidentialMixin
        # for the special logic required for Proposal objects
        if self.confidential_reason is None:
            if self.issue.is_confidential is True:
                self.is_confidential = True
            else:
                self.is_confidential = False
        else:
            self.is_confidential = True

    @property
    def arguments_for(self):
        return sorted(
            ProposalVoteArgument.objects.filter(proposal_vote__in=self.votes.filter(value=ProposalVoteValue.PRO)),
            key=lambda a: a.argument_score, reverse=True)

    @property
    def arguments_against(self):
        return sorted(
            ProposalVoteArgument.objects.filter(proposal_vote__in=self.votes.filter(value=ProposalVoteValue.CON)),
            key=lambda a: a.argument_score, reverse=True)

    @property
    def elegantly_interleaved_for_and_against_arguments(self):
        if not self.arguments_for:
            return list(self.arguments_against)
        if not self.arguments_against:
            return list(self.arguments_for)
        a = list(self.arguments_against)
        b = list(self.arguments_for)
        b, a = sorted((a, b), key=len)
        len_ab = len(a) + len(b)
        groups = groupby(((a[len(a) * i // len_ab], b[len(b) * i // len_ab]) for i in range(len_ab)),
                         key=lambda x: x[0])
        return [j[i] for k, g in groups for i, j in enumerate(g)]


@python_2_unicode_compatible
class ProposalVote(models.Model):
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"), related_name="votes")
    value = models.SmallIntegerField(_("Vote"), choices=ProposalVoteValue.CHOICES, default=ProposalVoteValue.NEUTRAL)

    @property
    def is_confidential(self):
        return self.proposal.is_confidential

    class Meta:
        unique_together = (("proposal", "user"),)
        verbose_name = _("Proposal Vote")
        verbose_name_plural = _("Proposal Votes")

    def __str__(self):
        return "%s | %s - %s (%s)" % (
            self.proposal.issue.title, self.proposal.title, self.user.display_name, self.get_value_display())


@python_2_unicode_compatible
class ProposalVoteArgument(models.Model):
    proposal_vote = models.ForeignKey(ProposalVote, on_delete=models.CASCADE, related_name='arguments')
    argument = models.TextField(verbose_name=_("Argument"))
    created_at = models.DateTimeField(_("Create at"), auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   related_name="arguments_created",
                                   verbose_name=_("Created by"))

    class Meta:
        verbose_name = _("Proposal vote argument")
        verbose_name_plural = _("Proposal vote arguments")

    def __str__(self):
        return self.argument

    @models.permalink
    def get_delete_url(self):
        return "delete_proposal_argument", (
            self.proposal_vote.proposal.issue.committee.community.slug,
            self.proposal_vote.proposal.issue.committee.slug,
            self.id)

    @models.permalink
    def get_edit_url(self):
        return "edit_proposal_argument", (
            self.proposal_vote.proposal.issue.committee.community.slug,
            self.proposal_vote.proposal.issue.committee.slug,
            self.id)

    @models.permalink
    def get_data_url(self):
        return "get_argument_value", (
            self.proposal_vote.proposal.issue.committee.community.slug,
            self.proposal_vote.proposal.issue.committee.slug,
            self.id)

    @models.permalink
    def get_vote_url(self):
        return "argument_up_down_vote", (
            self.proposal_vote.proposal.issue.committee.community.slug,
            self.proposal_vote.proposal.issue.committee.slug,
            self.id)

    @property
    def argument_for_ranking(self):
        pro = ProposalVoteArgumentRanking.objects.filter(argument=self, value=ProposalVoteValue.PRO).count()
        return pro

    @property
    def argument_against_ranking(self):
        against = ProposalVoteArgumentRanking.objects.filter(argument=self, value=ProposalVoteValue.CON).count()
        return against

    @property
    def argument_score(self):
        score = self.argument_for_ranking - self.argument_against_ranking
        return score


class ProposalVoteArgumentRanking(models.Model):
    argument = models.ForeignKey(ProposalVoteArgument, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("User"), related_name="argument_votes")
    value = models.SmallIntegerField(_("Vote"), choices=ProposalVoteArgumentVoteValue.CHOICES)

    class Meta:
        verbose_name = _("Proposal vote argument ranking")
        verbose_name_plural = _("Proposal vote arguments ranking")


class VoteResult(models.Model):
    """ straw vote result per proposal, per meeting """
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name="results")
    meeting = models.ForeignKey('meetings.Meeting', on_delete=models.CASCADE)
    votes_pro = models.PositiveIntegerField(_("Votes pro"))
    votes_con = models.PositiveIntegerField(_("Votes con"))
    community_members = models.PositiveIntegerField(_("Community members"))

    @property
    def is_confidential(self):
        return self.proposal.is_confidential

    class Meta:
        unique_together = (('proposal', 'meeting'),)
        verbose_name = _("Vote result")
        verbose_name_plural = _("Vote results")


class IssueRankingVote(models.Model):
    voted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='ranking_votes')
    rank = models.PositiveIntegerField()

    @property
    def is_confidential(self):
        return self.issue.is_confidential

        # TODO: add unique_together = (
        # ('voted_by', 'issue'),
        # and maybe: ('voted_by', 'rank')
        # )


@receiver(post_save, sender=Issue)
def set_confidential_on_relations(sender, instance, created,
                                  dispatch_uid='set_confidential_on_relations',
                                  **kwargs):
    # we need to ensure that relations implementing ConfidentialMixin or
    # ConfidentialByRelationMixin also have is_confidential set correctly.
    # At present, these are Proposal and AgendaItem

    for agenda_item in instance.agenda_items.all():
        # AgendaItem implements ConfidentialByRelationMixin,
        # so we call save to trigger the tracking logic.
        agenda_item.save()

    for proposal in instance.proposals.all():
        # Proposal implements ConfidentialMixin, so we need to call save to
        # trigger the confidential tracking logic.
        proposal.save()
