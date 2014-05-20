from itertools import chain
from django.contrib import messages
from django.http.response import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from issues.views import CommunityMixin
from issues.models import Issue, IssueStatus
from meetings import models
from meetings.forms import CloseMeetingForm
from ocd.base_views import AjaxFormView


class MeetingMixin(CommunityMixin):

    model = models.Meeting

    def get_queryset(self):
        return models.Meeting.objects.filter(community=self.community)


class MeetingList(MeetingMixin, RedirectView):
    required_permission = 'meetings.view_meeting'

    def get_redirect_url(self, **kwargs):
        o = models.Meeting.objects.filter(community=self.community).latest('held_at')
        if o:
            return o.get_absolute_url()


class MeetingDetailView(MeetingMixin, DetailView):
    required_permission = 'meetings.view_meeting'

    def get_context_data(self, **kwargs):
        d = super(MeetingDetailView, self).get_context_data(**kwargs)
        o = self.get_object()
        d['guest_list'] = o.get_guest_list()
        d['total_participants'] = len(d['guest_list']) + o.participations \
                                    .filter(is_absent=False).count()
        return d


class MeetingProtocolView(MeetingMixin, DetailView):
    required_permission = 'meetings.view_meeting'
    template_name = "emails/protocol.html"

    def get_context_data(self, **kwargs):
        context = super(MeetingProtocolView, self).get_context_data(**kwargs)
        agenda_items = context['object'].agenda.all()
        item_attachments = [item.issue.current_attachments(item) for item in agenda_items]
        context['attachments'] = list(chain.from_iterable(item_attachments))
        return context


class MeetingCreateView(AjaxFormView, MeetingMixin, CreateView):
    """actualy, this view handles the "close meeting" form.
       meeting objects are created only after this act """

    required_permission = 'meetings.add_meeting'

    template_name = "meetings/meeting_close.html"
    form_class = CloseMeetingForm

    def get_initial(self):
        d = super(MeetingCreateView, self).get_initial()
        dt = self.community.upcoming_meeting_scheduled_at
        if not dt or dt > timezone.now():
            dt = timezone.now().replace(second=0)
        d["held_at"] = dt
        return d

    def get_context_data(self, **kwargs):
        d = super(MeetingCreateView, self).get_context_data(**kwargs)
        participants = self.community.upcoming_meeting_participants.all()
        d['no_participants'] = True if not participants else False
        return d

    def get_form_kwargs(self):
        kwargs = super(MeetingCreateView, self).get_form_kwargs()
        kwargs['issues'] = self.community.upcoming_issues()
        return kwargs


    def form_valid(self, form):
        # archive selected issues
        m = self.community.close_meeting(form.instance, self.request.user)
        Issue.objects.filter(id__in=form.cleaned_data['issues']).update(
                  completed=True, status=IssueStatus.ARCHIVED)
        total = self.community.send_mail('protocol', self.request.user,
                            form.cleaned_data['send_to'], {'object': m})
        messages.info(self.request, _("Sending to %d users") % total)
        return HttpResponse(m.get_absolute_url())
