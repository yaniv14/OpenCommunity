from django.contrib import admin
from django.contrib.admin import site
from meetings import models


class AgendaItemInline(admin.TabularInline):
    model = models.AgendaItem
    extra = 0


class MeetingParticipantInline(admin.TabularInline):
    model = models.MeetingParticipant
    extra = 0


class MeetingExternalParticipantInline(admin.TabularInline):
    model = models.MeetingExternalParticipant
    extra = 0


class MeetingAdmin(admin.ModelAdmin):
    inlines = [
        MeetingParticipantInline,
        MeetingExternalParticipantInline,
        AgendaItemInline,
    ]

    list_display = (
                    '__unicode__',
                    'community',
                    )
    
    list_filter = (
                        'community',
                        'participants',
                        'guests',
                        )

    list_filter = (
                    'community',
                    'participants',
                    'guests',
                    )


class MeetingParticipantAdmin(admin.ModelAdmin):
    model = models.MeetingParticipant
    # date_hierarchy = 'meeting__held_at'
    list_display =  ('meeting', 'display_name', 'was_missing',) 
    list_filter = (
                        'meeting__community',
                        'display_name',
                        'is_absent',
                        )

    def was_missing(self, obj):
        return not obj.is_absent
    was_missing.boolean = True
    was_missing.short_description = 'attended'


site.register(models.Meeting, MeetingAdmin)
site.register(models.AgendaItem)
site.register(models.MeetingParticipant, MeetingParticipantAdmin)
