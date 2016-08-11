from django.utils.translation import ugettext_lazy as _


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

    choices = (
        (VIEWER, _('Viewer')),
        (OBSERVER, _('Observer')),
        (PARTICIPANT, _('Participant')),
        (PROPOSER, _('Proposer')),
        (CONTRIBUTOR, _('Contributor')),
        (EDITOR, _('Editor')),
        (OPERATOR, _('Operator')),
        (DECIDER, _('Decider')),
        (MANAGER, _('Manager')),
    )

    permissions = {}

    permissions[VIEWER] = [
        'access_community',
        'access_committee',
        'viewclosed_issue',
        'viewclosed_proposal',
        'view_meeting',
    ]

    permissions[OBSERVER] = permissions[VIEWER] + [
        'viewopen_issue',
        'viewopen_proposal',
        'viewupcoming_community',
        'vote',
        'proposal_board_vote_self',
        'vote_ranking',
    ]

    permissions[PARTICIPANT] = permissions[OBSERVER] + [
        'view_proposal_in_discussion',
        'viewupcoming_draft',
        'view_referendum_results',
        'view_update_status',
        'view_straw_vote_result',
        'view_confidential',
    ]

    permissions[PROPOSER] = permissions[PARTICIPANT] + [
        'add_proposal',
    ]

    permissions[CONTRIBUTOR] = permissions[PROPOSER] + [
        'add_issue',
    ]

    permissions[EDITOR] = permissions[CONTRIBUTOR] + [
        'editopen_issue',
        'editopen_proposal',
        'edittask_proposal',
    ]

    permissions[OPERATOR] = permissions[CONTRIBUTOR] + [
        'add_issuecomment',
        'edittask_proposal',
        'editupcoming_community',
        'editparticipants_community',
        'editsummary_community',  # ???
        'invite_member',
        'move_to_referendum',
        'proposal_board_vote',
    ]

    permissions[DECIDER] = permissions[OPERATOR] + [
        'editopen_issuecomment',
        'editagenda_community',
        'acceptopen_proposal',
        'add_meeting',  # == Close Meeting
        'edit_referendum',
        'chairman_vote',
        'show_member_profile',
    ]

    permissions[MANAGER] = permissions[DECIDER] + [
        'editopen_issue',
        'editclosed_issue',
        'editclosed_issuecomment',
        'editopen_proposal',
        'editclosed_proposal',
        'acceptclosed_proposal',
    ]


class DefaultGroups(object):
    MEMBER = "member"
    BOARD = "board"
    SECRETARY = "secretary"
    CHAIRMAN = "chairman"

    builtin = {
        MEMBER: [DefaultRoles.OBSERVER],
        BOARD: [DefaultRoles.PARTICIPANT],
        SECRETARY: [DefaultRoles.OPERATOR],
        CHAIRMAN: [DefaultRoles.DECIDER, DefaultRoles.EDITOR]
    }

    permissions = {
        k: frozenset(
            [p for role in roles for p in DefaultRoles.permissions[role]])
        for k, roles in builtin.items()
    }

    CHOICES = (
        (MEMBER, _("member")),
        (BOARD, _("board")),
        (SECRETARY, _("secretary")),
        (CHAIRMAN, _("chairman")),
    )


ALL_PERMISSIONS = frozenset(
    [p for perms in DefaultGroups.permissions.values() for p in perms])
