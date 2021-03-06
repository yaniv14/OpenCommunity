from django.conf.urls import url
from . import views


urlpatterns = [

    url(r'^$', views.MembershipList.as_view(), name="members"),
    url(r'^groups/$', views.MembershipGroupList.as_view(), name="members_groups"),
    url(r'^groups/add/$', views.GroupMembersUpdateView.as_view(), name="members_groups_update"),
    url(r'^community-remove/$', views.MembersCommunityRemoveView.as_view(), name="members_community_remove"),
    url(r'^create-invitation/$', views.CreateInvitationView.as_view(), name="create_invitation"),
    url(r'^(?P<pk>\d+)/$', views.MemberProfile.as_view(), name="member_profile"),
    url(r'^(?P<pk>\d+)/delete-invitation/$', views.DeleteInvitationView.as_view(), name="delete_invitation"),
    url(r'^autocomp/$', views.AutocompleteMemberName.as_view(), name="ac_user"),
    url(r'^import/$', views.ImportInvitationsView.as_view(), name="import_invitations"),

]
