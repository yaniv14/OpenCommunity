from communities import models
from django.contrib.admin import site
from django.contrib.admin.options import ModelAdmin, TabularInline
from users.models import CommunityMembership, CommitteeMembership


class CommunityConfidentialReasonInline(TabularInline):
    model = models.CommunityConfidentialReason
    fk_name = 'community'
    extra = 0


class CommunityGroupRoleInline(TabularInline):
    model = models.CommunityGroupRole
    extra = 0


class CommunityGroupInline(TabularInline):
    model = models.CommunityGroup
    extra = 0


class CommitteeInline(TabularInline):
    model = models.Committee
    fields = ('name', 'slug', 'is_public')
    extra = 0


class CommunityMembershipInline(TabularInline):
    model = CommunityMembership
    fk_name = 'community'
    extra = 0


class CommitteeMembershipInline(TabularInline):
    model = CommitteeMembership
    fk_name = 'committee'
    extra = 0


class CommunityAdmin(ModelAdmin):

    fields = ('name', 'slug', 'official_identifier', 'logo', 'is_public',
              'straw_voting_enabled', 'issue_ranking_enabled',
              'allow_links_in_emails', 'register_missing_board_members',
              'email_invitees', 'inform_system_manager', 'no_meetings_community')

    inlines = [CommitteeInline, CommunityConfidentialReasonInline, CommunityMembershipInline, CommunityGroupInline]


class CommitteeAdmin(ModelAdmin):
    list_display = ['community', 'name', 'slug']
    list_display_links = ['community', 'name', 'slug']
    fields = ('community', 'name', 'slug', 'official_identifier', 'logo', 'is_public',
              'straw_voting_enabled', 'issue_ranking_enabled',
              'allow_links_in_emails', 'register_missing_board_members',
              'email_invitees', 'inform_system_manager', 'no_meetings_committee')

    inlines = [CommitteeMembershipInline]


class CommunityGroupRoleAdmin(ModelAdmin):
    list_display = ['committee', 'group', 'role']
    list_display_links = ['committee', 'group', 'role']


class CommunityGroupAdmin(ModelAdmin):
    list_display = ['community', 'title']
    list_display_links = ['community', 'title']


class GroupUserAdmin(ModelAdmin):
    list_display = ['group', 'user']
    list_display_links = ['group', 'user']


site.register(models.Community, CommunityAdmin)
site.register(models.Committee, CommitteeAdmin)
site.register(models.CommunityGroup, CommunityGroupAdmin)
site.register(models.CommunityGroupRole, CommunityGroupRoleAdmin)
site.register(models.GroupUser, GroupUserAdmin)
