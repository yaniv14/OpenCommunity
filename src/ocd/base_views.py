from communities.models import Community
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.http.response import HttpResponseForbidden, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from users.models import Membership
from users.permissions import has_community_perm, get_community_perms
import json


def json_response(content, *args, **kwargs):
    kwargs['content_type'] = 'application/json'
    return HttpResponse(json.dumps(content), *args, **kwargs)


class LoginRequiredMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class ProtectedMixin(object):

    required_permission = None
    required_permission_for_post = None

    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated():
            if not self.community.is_public:
                return redirect_to_login(request.build_absolute_uri())

        if hasattr(self, 'get_required_permission'):
            perm = self.get_required_permission()
        else:
            perm = self.required_permission or "communities.access_community"

        if not has_community_perm(request.user, self.community, perm):
            if settings.DEBUG:
                return HttpResponseForbidden("403 %s" % perm)
            return HttpResponseForbidden("403 Unauthorized")  # TODO: raise PermissionDenied

        if request.method == "POST":
            if hasattr(self, 'get_required_permission_for_post'):
                perm = self.get_required_permission_for_post()
            else:
                perm = self.required_permission_for_post or "communities.access_community"

            if not has_community_perm(request.user, self.community, perm):
                if settings.DEBUG:
                    return HttpResponseForbidden("403 POST %s" % perm)
                return HttpResponseForbidden("403 Unauthorized")

        resp = super(ProtectedMixin, self).dispatch(request, *args, **kwargs)

        # Disable client side cache
        resp['Expires'] = '0'
        resp['Pragma'] = 'no-cache'
        resp['Cache-Control'] = 'no-cache, no-store, must-revalidate'

        return resp

    def get_context_data(self, **kwargs):
        d = super(ProtectedMixin, self).get_context_data(**kwargs)
        d['cperms'] = get_community_perms(self.request.user, self.community)
        return d


class CommunityMixin(ProtectedMixin):

    _community = None

    @property
    def community(self):
        if not self._community:
            self._community = get_object_or_404(Community, pk=self.kwargs['community_id'])
        return self._community

    def get_context_data(self, **kwargs):
        context = super(CommunityMixin, self).get_context_data(**kwargs)
        context['community'] = self.community
        context['is_member'] = Membership.objects.filter(community=self.community, user=self.request.user).exists() if self.request.user.id else False
        return context


class AjaxFormView(object):
    """ a mixin used for ajax based forms.  see `forms.js`."""

    reload_on_success = False

    def form_valid(self, form):
        """ returns link to redirect or empty string to reload as text/html """
        self.object = form.save()
        if hasattr(self, 'on_success'):
            self.on_success(form)
        url = "" if self.reload_on_success else self.get_success_url()
        return HttpResponse(url)

    def form_invalid(self, form):
        """ returns an 403 http response with form, including errors, as
        text/html """
        resp = super(AjaxFormView, self).form_invalid(form)
        resp.status_code = 403
        return resp
