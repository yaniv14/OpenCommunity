from django import template
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from issues.models import Proposal, ProposalVote, VoteResult, ProposalVoteArgument, ProposalVoteArgumentRanking
from meetings.models import Meeting
from users.models import OCUser

register = template.Library()


@register.filter
def voted_on(u, proposal_id):
    voted = ProposalVote.objects.filter(
        proposal_id=proposal_id,
        user_id=u.id).exists()
    return voted


@register.filter
def vote_percentage(proposal):
    if proposal.votes_pro is None:
        return 'undefined'
    votes = proposal.votes_pro + proposal.votes_con
    print votes, proposal.community_members
    percentage = (float(votes) / float(proposal.community_members)) * 100.0
    return round(percentage)


@register.simple_tag(takes_context=True)
def user_votes_on_issue(context):
    issue = context['i']
    user_id = context['user'].id
    proposals = Proposal.objects.open().filter(issue_id=issue.id)
    votes_cnt = ProposalVote.objects.filter(
        proposal__in=proposals,
        user_id=user_id).count()
    if proposals.count() == 0:
        return mark_safe("<span></span>")
    elif votes_cnt == proposals.count():
        return mark_safe("<span class='badge no-vote-badge'>{0}/{1}</span>".format(votes_cnt, proposals.count()))
    else:
        return mark_safe("<span class='badge vote-badge'>{0}/{1}</span>".format(votes_cnt, proposals.count()))


@register.filter
def prev_straw_results_link(proposal, meeting_id=None):
    link_args = {
        'community_slug': proposal.issue.committee.community.slug,
        'committee_slug': proposal.issue.committee.slug,
        'pk': proposal.id,
    }
    url = reverse('vote_results_panel', kwargs=link_args)
    if meeting_id:
        cur_meeting = get_object_or_404(Meeting, id=meeting_id)
        prev_res = VoteResult.objects.filter(proposal=proposal,
                                             meeting__held_at__lt=cur_meeting.held_at).order_by('-meeting__held_at')

        if prev_res.count():
            return '{0}?meeting_id={1}&dir=prev'.format(url, prev_res[0].meeting_id)
    else:
        # get meeting from last VoteResult object
        try:
            result = VoteResult.objects.filter(proposal=proposal).latest('meeting__held_at')
            return '{0}?meeting_id={1}&dir=prev'.format(url, result.meeting.id)
        except VoteResult.DoesNotExist:
            pass

    return ''


@register.filter
def next_straw_results_link(proposal, meeting_id):
    c = proposal.issue.committee
    link_args = {
        'community_slug': proposal.issue.committee.community.slug,
        'committee_slug': proposal.issue.committee.slug,
        'pk': proposal.id,
    }
    url = reverse('vote_results_panel', kwargs=link_args)
    if meeting_id:
        cur_meeting = get_object_or_404(Meeting, id=meeting_id)
        next_res = VoteResult.objects.filter(proposal=proposal,
                                             meeting__held_at__gt=cur_meeting.held_at).order_by('meeting__held_at')
        if next_res.count():
            return '{0}?meeting_id={1}&dir=next'.format(url, next_res[0].meeting_id)
        elif proposal.has_votes and \
                proposal.issue.is_upcoming and \
                c.straw_vote_ended and \
                c.upcoming_meeting_is_published:
            return '{0}?meeting_id=&dir=next'.format(url)
    else:
        pass
    return ''


@register.filter
def subtract(value, arg):
    if arg is None:
        return value
    return value - arg


@register.filter
def nutral_votes(proposal):
    if proposal.votes_pro is None:
        return 'undefined'
    votes = proposal.votes_pro + proposal.votes_con
    return proposal.community_members - votes


@register.filter
def user_proposal_vote_id(proposal_id, user_id):
    user = OCUser.objects.get(pk=user_id)
    proposal = Proposal.objects.get(pk=proposal_id)
    return ProposalVote.objects.get(proposal=proposal, user=user).id


@register.filter
def user_vote_result(proposal_id, user_id):
    user = OCUser.objects.get(pk=user_id)
    proposal = Proposal.objects.get(pk=proposal_id)
    vote = ProposalVote.objects.get(proposal=proposal, user=user)
    if vote.value == 1:
        return "pro"
    elif vote.value == -1:
        return "con"
    else:
        return None


@register.filter
def user_ranked_argument(argument_id, user_id):
    user = OCUser.objects.get(pk=user_id)
    argument = ProposalVoteArgument.objects.get(pk=argument_id)
    try:
        vote = ProposalVoteArgumentRanking.objects.get(argument=argument, user=user)
        return "pro" if vote.value == 1 else "con"
    except ProposalVoteArgumentRanking.DoesNotExist:
        return False


@register.filter
def user_argued(proposal, user_id):
    user = OCUser.objects.get(pk=user_id)
    return ProposalVoteArgument.objects.filter(proposal_vote__proposal=proposal, created_by=user).exists()
