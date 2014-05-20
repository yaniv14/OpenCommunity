from django.http.response import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from shultze.models import IssuesGraph
from issues.models import Issue, IssueRankingVote
from ocd.base_views import json_response
import json


def user_vote(community_id, current_vote, prev_vote=[]):
    try:
        g = IssuesGraph.objects.get(community_id=community_id)
    except IssuesGraph.DoesNotExist:
        g = IssuesGraph.objects.create(community_id=community_id)
        g.initialize_graph()
    if prev_vote:
        g.add_ballots(prev_vote,reverse=True)
    g.add_ballots(current_vote)


def set_issues_order_by_votes(community_id):
    Issue.objects.filter(community_id=community_id).update(\
        order_by_votes=9999)
    try:
        g = IssuesGraph.objects.get(community_id=community_id)
    except IssuesGraph.DoesNotExist:
        raise

    order = g.get_schulze_npr_order_and_rating_bottom_up_sum()
    min_obj = order[0].keys()[0]
    max_obj = order[-1].keys()[0]
    min_likes = IssueRankingVote.objects.filter(issue__id=min_obj, rank__gt=1).count()
    max_likes = IssueRankingVote.objects.filter(issue__id=max_obj, rank__gt=1).count()
    normorder = g.normalize_ordered_rating_bottom_up_sum(order, min_likes, max_likes)

    issues = Issue.objects.in_bulk([i.keys()[0] for i in normorder])
    for id_entry in normorder:
        id = id_entry.keys()[0]
        issues[id].order_by_votes = id_entry[id]
        print issues[id].title, id_entry[id]
        issues[id].save()


def send_issue_ranking(request):
    if request.POST:
        cid = request.POST['community_id']
        current_vote = json.loads(request.POST.get('new_order'))
        prev_vote = IssueRankingVote.objects.filter(
                            voted_by=request.user,
                            issue__community_id=cid) \
                            .order_by('rank')
        
        if current_vote:
            prev_param = {'ballot': [], 'count': 1, }
            current_param = {'ballot': [], 'count': 1, }
            if prev_vote:
                prev_vote_as_list = list(prev_vote.values_list('issue_id', flat=True))
                for v in prev_vote:
                    v.delete()

                for v in prev_vote_as_list:
                    prev_param['ballot'].append([v])
                prev_param = [prev_param,]
            else:
                prev_param = None

            for i, v in enumerate(current_vote):
                IssueRankingVote.objects.create(
                    voted_by=request.user,
                    issue_id=v,
                    rank=i
                )
                current_param['ballot'].append([v])
            remaining_issues = Issue.objects.filter(community_id=cid, active=True) \
                                            .exclude(id__in=current_vote)
            # current_param['ballot'].append([issue.id for issue in remaining_issues])
            current_param = [current_param,]
            # print current_param, prev_param
            user_vote(cid, current_param, prev_param)
            set_issues_order_by_votes(request.POST['community_id'])
            return HttpResponse(json_response('ok'))


