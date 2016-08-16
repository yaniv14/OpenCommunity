import json

from communities.models import CommunityGroup, GroupUser
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseBadRequest, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _, gettext
from django.views.decorators.csrf import csrf_protect
from django.views.generic import FormView, CreateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from ocd import settings
from ocd.base_views import CommunityMixin, AjaxFormView
from users import models
from acl.default_roles import DefaultGroups
from users.forms import InvitationForm, QuickSignupForm, ImportInvitationsForm, MembersGroupsForm, \
    MembersCommunityRemoveForm
from users.models import Invitation, OCUser, CommunityMembership


class MembershipMixin(CommunityMixin):
    model = models.CommunityMembership

    def get_queryset(self):
        return models.CommunityMembership.objects.filter(community=self.community)

    def validate_invitation(self, email):
        # somewhat of a privacy problem next line. should probably fail silently
        if CommunityMembership.objects.filter(community=self.community, user__email=email).exists():
            return HttpResponseBadRequest(_("This user already a member of this community."))

        if Invitation.objects.filter(community=self.community, email=email).exists():
            return HttpResponseBadRequest(_("This user is already invited to this community."))
        return None


class MembershipList(MembershipMixin, ListView):
    required_permission = 'invite_member'

    def get_context_data(self, **kwargs):
        d = super(MembershipList, self).get_context_data(**kwargs)

        d['invites'] = Invitation.objects.filter(community=self.community)
        d['form'] = InvitationForm(initial={'message':
                                                Invitation.DEFAULT_MESSAGE %
                                                self.community.name})
        d['form'].fields['groups'].queryset = CommunityGroup.objects.filter(community=self.community).exclude(
            title='administrator')
        d['members'] = CommunityMembership.objects.filter(community=self.community).order_by('group_name')
        # d['board_list'] = Membership.objects.board().filter(community=self.community)
        # d['member_list'] = Membership.objects.none_board().filter(community=self.community)
        # d['board_name'] = self.community.name

        return d

    def post(self, request, *args, **kwargs):

        form = InvitationForm(request.POST)

        if not form.is_valid():
            return HttpResponseBadRequest(
                _("Form error. Please supply a valid email."))

        v_err = self.validate_invitation(form.instance.email)
        if v_err:
            return v_err

        form.instance.community = self.community
        form.instance.created_by = request.user

        i = form.save()
        i.send(sender=request.user, recipient_name=form.cleaned_data['name'])

        return render(request, 'users/_invitation.html', {'object': i})


class DeleteInvitationView(CommunityMixin, DeleteView):
    required_permission = 'invite_member'

    model = models.Invitation

    def get_queryset(self):
        return self.model.objects.filter(community=self.community)

    def get(self, request, *args, **kwargs):
        return HttpResponse("?")

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponse("OK")


class AcceptInvitationView(DetailView):
    slug_field = 'code'
    slug_url_kwarg = 'code'
    model = models.Invitation

    form = None

    def get_form(self):
        if self.request.method == "POST":
            return QuickSignupForm(self.request.POST)
        else:
            return QuickSignupForm(initial={'display_name': self.get_object().name})

    def get_context_data(self, **kwargs):
        d = super(AcceptInvitationView, self).get_context_data(**kwargs)
        d['user_exists'] = OCUser.objects.filter(email=self.get_object().email).exists()
        d['path'] = self.request.path
        d['login_path'] = reverse('login') + "?next=" + self.request.path
        d['form'] = self.form if self.form else self.get_form()
        return d

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return render(request, 'users/invitation404.html', {'base_url': settings.HOST_URL})
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        i = self.get_object()

        def create_membership(user):
            # Create community membership
            obj, created = CommunityMembership.objects.get_or_create(user=user, community=i.community)
            if created:
                obj.invited_by = i.created_by
                obj.save()
            # Create all group user & committee membership
            for group in i.groups.all():
                group_user_obj, group_user_created = GroupUser.objects.get_or_create(group=group, user=user)
                if group_user_created:
                    group_user_obj.created_by = i.created_by
                    group_user_obj.save()
                # TODO: assign member to committee?
            i.delete()
            return obj

        if request.user.is_authenticated():
            if 'join' in request.POST:
                m = create_membership(request.user)
                return redirect(m.community.get_absolute_url())

        else:
            if 'signup' in request.POST:
                self.form = self.get_form()
                if self.form.is_valid():
                    # Quickly create a user :-)
                    self.form.instance.email = i.email
                    u = self.form.save()
                    m = create_membership(u)
                    # TODO Send email with details
                    user = authenticate(email=self.form.instance.email,
                                        password=self.form.cleaned_data['password1'])
                    login(request, user)
                    return redirect(m.community.get_absolute_url())

        messages.warning(request,
                         _("Oops. Something went wrong. Please try again."))
        return self.get(request, *args, **kwargs)


class AutocompleteMemberName(MembershipMixin, ListView):
    required_permission = 'editopen_issue'

    def get_queryset(self):
        members = super(AutocompleteMemberName, self).get_queryset()
        limit = self.request.GET.get('limit', '')
        if limit == 'm':
            members = members.filter(default_group_name='member')
        q = self.request.GET.get('q', '')
        if q:
            members = members.filter(
                user__is_active=True,
                user__display_name__istartswith=q)
        else:
            members = members.filter(user__is_active=True)
            if members.count() > 75:
                return None

        return members

    def get(self, request, *args, **kwargs):

        def _cmp_func(a, b):
            res = cmp(a['board'], b['board']) * -1
            if res == 0:
                return cmp(a['value'], b['value'])
            else:
                return res

        members = self.get_queryset()
        if not members:
            return HttpResponse(json.dumps({}))
        else:
            members = list(members.values('user__display_name', 'user__id'))
            for m in members:
                m['tokens'] = [m['user__display_name'], ]
                m['value'] = m['user__display_name']
                # m['board'] = m['default_group_name'] != 'member'
            members.sort(_cmp_func)
            # context = self.get_context_data(object_list=members)
            return HttpResponse(json.dumps(members), {'content_type': 'application/json'})


class MemberProfile(MembershipMixin, DetailView):
    required_permission = 'show_member_profile'

    model = models.CommunityMembership
    template_name = "users/member_profile.html"

    def get_context_data(self, **kwargs):
        d = super(MemberProfile, self).get_context_data(**kwargs)
        d['form'] = ""
        d['belongs_to_board'] = self.get_object().default_group_name != DefaultGroups.MEMBER
        d['member_late_tasks'] = self.object.member_late_tasks(user=self.request.user, community=self.community)
        d['member_open_tasks'] = self.object.member_open_tasks(user=self.request.user, community=self.community)
        d['member_close_tasks'] = self.object.member_close_tasks(user=self.request.user, community=self.community)
        return d


class ImportInvitationsView(MembershipMixin, FormView):
    form_class = ImportInvitationsForm
    template_name = 'users/import_invitations.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(import_invitation_form=self.get_form(self.form_class)))

    def form_valid(self, form):
        msg = 'def message'
        def_enc = 'windows-1255'
        uploaded = form.cleaned_data['csv_file']

        # CHOICES is a tuple of role names: (name, _(name))
        roles = dict(DefaultGroups.CHOICES)
        sent = 0
        final_rows = []
        partial = ''
        composite = False
        for chunk in uploaded.chunks():
            rows = chunk.split('\n')
            for i, row in enumerate(rows):
                if row.startswith('"'):
                    composite = True
                    partial = row[1:]
                elif composite:
                    partial += '\n' + row
                    if '"' in row:
                        composite = False
                        final_rows.append(partial[:partial.rindex('"')])
                else:
                    final_rows.append(row)

        for i, row in enumerate(final_rows):
            words = row.split(',')
            # print ' -- ', words[0], ' -- '
            if i == 0:
                msg = row
                try:
                    msg = msg.decode(def_enc)
                except UnicodeDecodeError:
                    def_enc = 'utf-8'
                    print 'UTF-8'
                    msg = msg.decode(def_enc)
            elif len(words) > 1:
                name = words[0].decode(def_enc)
                email = words[1].decode(def_enc)
                try:
                    role = words[2].strip().decode(def_enc)
                    for k, v in roles.items():
                        if v == role:
                            role = k
                except:
                    role = roles.keys()[0]
                if not role in roles.keys():
                    role = roles.keys()[0]

                v_err = self.validate_invitation(email)
                if v_err:
                    continue
                invitation = Invitation.objects.create(
                    community=self.community,
                    name=name,
                    email=email,
                    created_by=self.request.user,
                    default_group_name=role,
                    message=msg)
                try:
                    invitation.send(sender=self.request.user, recipient_name=name)
                    # time.sleep(1)
                    sent += 1
                except:
                    pass

        messages.success(self.request, _('%d Invitations sent') % (sent,))
        return redirect(reverse('members', kwargs={'community_id': self.community.id}))

    @method_decorator(permission_required('is_superuser'))
    def dispatch(self, *args, **kwargs):
        return super(ImportInvitationsView, self).dispatch(*args, **kwargs)


@csrf_protect
def oc_password_reset(request, is_admin_site=False,
                      template_name='registration/password_reset_form.html',
                      email_template_name='registration/password_reset_email.html',
                      subject_template_name='registration/password_reset_subject.txt',
                      password_reset_form=PasswordResetForm,
                      token_generator=default_token_generator,
                      post_reset_redirect=None,
                      from_email=None,
                      current_app=None,
                      extra_context=None):
    if post_reset_redirect is None:
        post_reset_redirect = reverse('django.contrib.auth.views.password_reset_done')
    if request.method == "POST":
        form = password_reset_form(request.POST)
        if form.is_valid():
            from_email = "%s <%s>" % (settings.FROM_EMAIL_NAME, settings.FROM_EMAIL)
            opts = {
                'use_https': request.is_secure(),
                'token_generator': token_generator,
                'from_email': from_email,
                'email_template_name': email_template_name,
                'subject_template_name': subject_template_name,
                'request': request,
            }
            if is_admin_site:
                opts = dict(opts, domain_override=request.get_host())
            form.save(**opts)
            return HttpResponseRedirect(post_reset_redirect)
        email = request.POST['email']
        try:
            invitation = Invitation.objects.get(email=email)
            extra_context = {
                'has_invitation': True,
            }
            invitation.send(sender=invitation.created_by,
                            recipient_name=invitation.name)
            # TODO: redirect to message
        # return HttpResponseRedirect(reverse('invitation_sent'))
        except Invitation.DoesNotExist:
            pass
    else:
        form = password_reset_form()
    context = {
        'form': form,
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)


class MembershipGroupList(MembershipMixin, ListView):
    template_name = 'users/membership_groups.html'
    required_permission = 'invite_member'
    context_object_name = 'members'

    def get_queryset(self):
        return models.CommunityMembership.objects.filter(community=self.community).order_by('user__display_name').distinct(
            'user__display_name')

    def get_context_data(self, **kwargs):
        d = super(MembershipGroupList, self).get_context_data(**kwargs)
        d['form'] = InvitationForm(initial={'message': Invitation.DEFAULT_MESSAGE % self.community.name})
        d['groups_list'] = CommunityGroup.objects.filter(community=self.community)
        return d

    def post(self, request, *args, **kwargs):

        form = InvitationForm(request.POST)

        if not form.is_valid():
            return HttpResponseBadRequest(
                _("Form error. Please supply a valid email."))

        v_err = self.validate_invitation(form.instance.email)
        if v_err:
            return v_err

        form.instance.community = self.community
        form.instance.created_by = request.user

        i = form.save()
        i.send(sender=request.user, recipient_name=form.cleaned_data['name'])

        return HttpResponse('')
        # return render(request, 'users/_invitation.html', {'object': i})


class GroupMembersUpdateView(AjaxFormView, CommunityMixin, FormView):
    form_class = MembersGroupsForm
    template_name = "users/member_update_form.html"
    reload_on_success = True
    required_permission = 'invite_member'

    def form_valid(self, form):
        members = list(set(form.cleaned_data['members'].split(',')))
        groups = form.cleaned_data['groups']
        action = int(self.request.GET.get('action', None))

        for g in groups:
            for u in members:
                if action == 1:
                    obj, created = GroupUser.objects.get_or_create(
                        user_id=int(u),
                        group_id=int(g)
                    )
                    if created:
                        obj.created_by = self.request.user
                        obj.save()
                elif action == 2:
                    try:
                        obj = GroupUser.objects.get(user_id=int(u), group_id=int(g))
                        obj.delete()
                    except GroupUser.DoesNotExist:
                        pass

        return super(GroupMembersUpdateView, self).form_valid(form)

    def get_form_kwargs(self):
        kwargs = super(GroupMembersUpdateView, self).get_form_kwargs()
        kwargs.update({'community': self.community})
        return kwargs


class MembersCommunityRemoveView(AjaxFormView, CommunityMixin, FormView):
    form_class = MembersCommunityRemoveForm
    template_name = "users/member_community_remove_form.html"
    reload_on_success = True
    required_permission = 'invite_member'

    def form_valid(self, form):
        members = list(set(form.cleaned_data['members'].split(',')))

        for u in members:
            try:
                objs = CommunityMembership.objects.filter(user_id=int(u), community=self.community)
                for obj in objs:
                    obj.delete()
            except:
                CommunityMembership.DoesNotExist

        return super(MembersCommunityRemoveView, self).form_valid(form)


class CreateInvitationView(AjaxFormView, MembershipMixin, CreateView):
    model = Invitation
    template_name = 'users/invitation_form.html'
    required_permission = 'invite_member'
    form_class = InvitationForm
    reload_on_success = True

    def get_initial(self):
        return {'message': Invitation.DEFAULT_MESSAGE % self.community.name}

    def get_form_kwargs(self):
        kwargs = super(CreateInvitationView, self).get_form_kwargs()
        kwargs.update({'community': self.community})
        return kwargs

    def form_valid(self, form):
        form.instance.community = self.community
        form.instance.created_by = self.request.user

        i = form.save()
        i.send(sender=self.request.user, recipient_name=form.cleaned_data['name'])
        return super(CreateInvitationView, self).form_valid(form)

    # def post(self, request, *args, **kwargs):
    #     form_class = self.get_form_class()
    #     form = self.get_form(form_class)
    #
    #     if not form.is_valid():
    #         return HttpResponseBadRequest(
    #             _("Form error. Please supply a valid email."))
    #
    #     # v_err = self.validate_invitation(form.instance.email)
    #     # if v_err:
    #     #     return v_err
    #
    #     form.instance.community = self.community
    #     form.instance.created_by = request.user
    #
    #     i = form.save()
    #     i.send(sender=request.user, recipient_name=form.cleaned_data['name'])
    #
    #     return HttpResponse('')
