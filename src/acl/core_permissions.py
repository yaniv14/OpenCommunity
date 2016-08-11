from django.utils.translation import ugettext_lazy as _

PERMISSIONS = (
    (
        'access_community',
        _('Access Community'),
        ()
    ),
    (
        'access_committee',
        _('Access Committee'),
        ()
    ),
    (
        'viewupcoming_community',
        _('View Upcoming Meeting'),
        ('access_community',)
    ),
    (
        'viewupcoming_committee',
        _('View Upcoming Meeting'),
        ('access_committee',)
    ),
    (
        'viewupcoming_draft',
        _('View Upcoming Meeting Before Published'),
        ('viewupcoming_community',)
    ),
    (
        'editagenda_community',
        _('Edit Upcoming Agenda'),
        ()
    ),
    (
        'editparticipants_community',
        _('Manage Upcoming Meeting Participants'),
        ()
    ),
    (
        'editsummary_community',
        _('Edit Summary'),
        ()
    ),
    (
        'editupcoming_community',
        _('Edit Upcoming'),
        ()
    ),
    (
        'invite_member',
        _('Invite Member'),
        ()
    ),
    (
        'acceptclosed_proposal',
        _('Acceptclosed Proposal'),
        ()
    ),
    (
        'acceptopen_proposal',
        _('Acceptopen Proposal'),
        ()
    ),
    (
        'add_issue',
        _('Add Issue'),
        ()
    ),
    (
        'add_issuecomment',
        _('Add Issuecomment'),
        ()
    ),
    (
        'add_proposal',
        _('Add Proposal'),
        ()
    ),
    (
        'chairman_vote',
        _('Chairman Vote'),
        ()
    ),
    (
        'edit_referendum',
        _('Edit Referendum'),
        ()
    ),
    (
        'editclosed_issue',
        _('Edit Closed Issue'),
        ()
    ),
    (
        'editclosed_issuecomment',
        _('Edit Closed Issuecomment'),
        ()
    ),
    (
        'editclosed_proposal',
        _('Edit Closed Proposal'),
        ()
    ),
    (
        'editopen_issue',
        _('Edit Open Issue'),
        ()
    ),
    (
        'editopen_issuecomment',
        _('Edit Open Issuecomment'),
        ()
    ),
    (
        'editopen_proposal',
        _('Edit Open Proposal'),
        ()
    ),
    (
        'edittask_proposal',
        _('Edit Task Proposal'),
        ()
    ),
    (
        'move_to_referendum',
        _('Move To Referendum'),
        ()
    ),
    (
        'proposal_board_vote',
        _('Proposal Board Vote'),
        ()
    ),
    (
        'proposal_board_vote_self',
        _('Proposal Board Vote Self'),
        ()
    ),
    (
        'view_proposal_in_discussion',
        _('View Proposal In Discussion'),
        ()
    ),
    (
        'view_referendum_results',
        _('View Referendum Results'),
        ()
    ),
    (
        'view_update_status',
        _('View Update Status'),
        ()
    ),
    (
        'view_straw_vote_result',
        _('View straw vote result'),
        ()
    ),
    (
        'viewclosed_issue',
        _('View Closed Issue'),
        ()
    ),
    (
        'viewclosed_proposal',
        _('View Closed Proposal'),
        ()
    ),
    (
        'viewopen_issue',
        _('View Open Issue'),
        ()
    ),
    (
        'viewopen_proposal',
        _('View Open Proposal'),
        ()
    ),
    (
        'vote',
        _('Vote'),
        ()
    ),
    (
        'vote_ranking',
        _('Vote Ranking'),
        ()
    ),
    (
        'add_meeting',
        _('Add Meeting'),
        ()
    ),
    (
        'view_meeting',
        _('View Meeting'),
        ()
    ),
    (
        'show_member_profile',
        _('Show Member Profile'),
        ()
    ),
    (
        'view_confidential',
        _('Can view confidential Issue/Proposal'),
        ()
    )
)

CHOICES = [x[:2] for x in PERMISSIONS]
CHOICES_DICT = dict(CHOICES)
ORDER = dict([(x[0], i) for i, x in enumerate(PERMISSIONS)])
