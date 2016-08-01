from communities import models
from django.contrib.admin import site
from django.contrib.admin.options import ModelAdmin, TabularInline
from users.models import CommunityMembership


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

    inlines = [CommunityGroupRoleInline]


class CommunityGroupRoleAdmin(ModelAdmin):
    list_display = ['committee', 'group', 'role']
    list_display_links = ['committee', 'group', 'role']


class CommunityGroupAdmin(ModelAdmin):
    list_display = ['community', 'title']
    list_display_links = ['community', 'title']


site.register(models.Community, CommunityAdmin)
site.register(models.Committee, CommitteeAdmin)
site.register(models.CommunityGroup, CommunityGroupAdmin)
site.register(models.CommunityGroupRole, CommunityGroupRoleAdmin)
