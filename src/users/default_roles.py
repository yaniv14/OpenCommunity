from django.utils.translation import ugettext_lazy as _
import itertools


class DefaultRoles(object):

    VIEWER = 'viewer'
    OBSERVER = 'observer'
    PARTICIPANT = 'participant'
    PROPOSER = 'proposer'
    CONTRIBUTOR = 'contributor'
    EDITOR = 'editor'
    OPERATOR = 'operator'
    DECIDER = 'decider'
    MANAGER = 'manager'

    permissions = {}

    permissions[VIEWER] = [
                           'communities.access_community',
                           'issues.viewclosed_issue',
                           'issues.viewclosed_proposal',
                           'meetings.view_meeting',
                           ]

    permissions[OBSERVER] = permissions[VIEWER] + [
                           'issues.viewopen_issue',
                           'issues.viewopen_proposal',
                           'communities.viewupcoming_community',
                           'issues.vote',
                           'issues.proposal_board_vote_self',
                           'issues.vote_ranking',
                          ]

    permissions[PARTICIPANT] = permissions[OBSERVER] + [
                            'issues.view_proposal_in_discussion',
                            'communities.viewupcoming_draft',
                            'issues.view_referendum_results',
                            'issues.view_update_status',
                          ]
     
    permissions[PROPOSER] = permissions[PARTICIPANT] + [
                           'issues.add_proposal',                          
                          ]

    permissions[CONTRIBUTOR] = permissions[PROPOSER] + [
                           'issues.add_issue',
                          ]

    permissions[EDITOR] = permissions[CONTRIBUTOR] + [
                           'issues.editopen_issue',
                           'issues.editopen_proposal',
                           'issues.edittask_proposal',
                          ]

    permissions[OPERATOR] = permissions[CONTRIBUTOR] + [
                           'issues.add_issuecomment',
                           'issues.edittask_proposal',
                           'community.editupcoming_community',
                           'community.editparticipants_community',
                           'community.editsummary_community', # ???
                           'community.invite_member',
                           'issues.move_to_referendum',
                           'issues.proposal_board_vote',
                          ]

    permissions[DECIDER] = permissions[OPERATOR] + [
                           'issues.editopen_issuecomment',
                           'community.editagenda_community',
                           'issues.acceptopen_proposal',
                           'meetings.add_meeting',  # == Close Meeting
                           'issues.edit_referendum',
                           'issues.chairman_vote',
                           'users.show_member_profile',
                          ]

    permissions[MANAGER] = permissions[DECIDER] + [
                           'issues.editopen_issue',
                           'issues.editclosed_issue',
                           'issues.editclosed_issuecomment',
                           'issues.editopen_proposal',
                           'issues.editclosed_proposal',
                           'issues.acceptclosed_proposal',
                          ]


class DefaultGroups(object):
    MEMBER = "member"
    BOARD = "board"
    SECRETARY = "secretary"
    CHAIRMAN = "chairman"

    permissions = {}

    permissions[MEMBER] = frozenset(DefaultRoles.permissions[DefaultRoles.OBSERVER])
    permissions[BOARD] = frozenset(DefaultRoles.permissions[DefaultRoles.PARTICIPANT])
    permissions[SECRETARY] = frozenset(DefaultRoles.permissions[DefaultRoles.OPERATOR])
    permissions[CHAIRMAN] = frozenset(DefaultRoles.permissions[DefaultRoles.DECIDER] +
                                DefaultRoles.permissions[DefaultRoles.EDITOR])
    CHOICES = (
                (MEMBER, _("member")),
                (BOARD, _("board")),
                (SECRETARY, _("secretary")),
                (CHAIRMAN, _("chairman")),
               )

ALL_PERMISSIONS = frozenset(itertools.chain(*DefaultGroups.permissions.values()))
