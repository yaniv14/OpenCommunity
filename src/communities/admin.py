from communities import models
from django.contrib.admin import site
from django.contrib.admin.options import ModelAdmin, TabularInline
from users.models import Membership


class CommunityMembershipInline(TabularInline):
    model = Membership
    fk_name = 'community'


class CommunityAdmin(ModelAdmin):

    fields = ('name', 'board_name', 'official_identifier', 'logo', 'is_public',
              'straw_voting_enabled', 'issue_ranking_enabled',
              'allow_links_in_emails', 'register_missing_board_members',
              'email_invitees', 'inform_system_manager')

    inlines = [CommunityMembershipInline]


site.register(models.Community, CommunityAdmin)
