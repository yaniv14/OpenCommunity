from django.conf.urls import patterns, url
from issues import views

urlpatterns = patterns('',

    url(r'^$', views.IssueList.as_view(), name="issues"),

    url(r'^create/$', views.IssueCreateView.as_view(), name="issue_create"),

    url(r'^upcoming-create/$', views.IssueCreateView.as_view(upcoming=True),

                                name="issue_create_upcoming"),

    url(r'^(?P<pk>\d+)/$', views.IssueDetailView.as_view(), name="issue"),

    url(r'^(?P<pk>\d+)/edit/$', views.IssueEditView.as_view(),
                                name="issue_edit"),

    url(r'^(?P<pk>\d+)/edit-abstract/$', views.IssueEditAbstractView.as_view(),
                                name="issue_edit_abstract"),

    url(r'^(?P<pk>\d+)/set-length/$', views.IssueSetLengthView.as_view(),
                                name="issue_set_length"),

    url(r'^(?P<pk>\d+)/complete/$', views.IssueCompleteView.as_view(),
                                name="issue_complete"),

    url(r'^(?P<pk>\d+)/delete/$', views.IssueDeleteView.as_view(),
                                name="issue_delete"),

    url(r'^(?P<pk>\d+)/attach/$', views.AttachmentCreateView.as_view(),
                                name="add_attachment"),

    url(r'^(?P<issue_id>\d+)/remove-attachment/(?P<pk>\d+)/$',
                                views.AttachmentDeleteView.as_view(),
                                name="attachment_delete"),

    url(r'^(?P<issue_id>\d+)/download-attachment/(?P<pk>\d+)/$',
                                views.AttachmentDownloadView.as_view(),
                                name="attachment_download"),

    url(r'^(?P<pk>\d+)/create-proposal/$', views.ProposalCreateView.as_view(),
            name="proposal_create"),

    url(r'^(?P<issue_id>\d+)/(?P<pk>\d+)/$',
        views.ProposalDetailView.as_view(), name="proposal"),

    url(r'^(?P<issue_id>\d+)/(?P<pk>\d+)/edit/$',
        views.ProposalEditView.as_view(), name="proposal_edit"),

    url(r'^(?P<issue_id>\d+)/(?P<pk>\d+)/delete/$',
        views.ProposalDeleteView.as_view(), name="proposal_delete"),

    url(r'^(?P<issue_id>\d+)/(?P<pk>\d+)/task_completed/$',
        views.ProposalCompletedTaskView.as_view(), name="task_completed"),

    url(r'^(?P<issue_id>\d+)/(?P<pk>\d+)/edit-task/$',
        views.ProposalEditTaskView.as_view(), name="proposal_edit_task"),

    url(r'^delete-comment/(?P<pk>\d+)/$',
        views.IssueCommentDeleteView.as_view(), name="delete_issue_comment"),

    url(r'^edit-comment/(?P<pk>\d+)/$',
        views.IssueCommentEditView.as_view(), name="edit_issue_comment"),

    url(r'^vote/(?P<pk>\d+)/$',
        views.ProposalVoteView.as_view(), name="vote_on_proposal"),

    url(r'^vote/(?P<pk>\d+)/multi/$',
        views.MultiProposalVoteView.as_view(), name="multi_votes_on_proposal"),

    url(r'^vote_res_panel/(?P<pk>\d+)/$',
        views.VoteResultsView.as_view(), name="vote_results_panel"),

    url(r'^(?P<issue_id>\d+)/set_register_votes/(?P<pk>\d+)/$',
        views.ChangeBoardVoteStatusView.as_view(), name="set_register_votes"),

    url(r'^autocomplete_tag/$',
        views.AutoCompleteTagView.as_view(), name="autocomplete_tag"),

    url(r'^assignments/$',
        views.AssignmentsView.as_view(), name="assignments"),

    url(r'^procedures/$',
        views.ProceduresView.as_view(), name="procedures"),
    

)
