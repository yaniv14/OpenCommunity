from django.conf import settings


def analytics(request):

    """OPENCOMMUNITY_ANALYTICS setup in the request context."""

    analytics = {
        'piwik': settings.OPENCOMMUNITY_ANALYTICS.get('piwik'),
        'ga': settings.OPENCOMMUNITY_ANALYTICS.get('ga')
    }

    return {'analytics': analytics}


def smart_404(request):

    """Returns a 404 message that tries to help the user."""

    base_url = settings.HOST_URL

    not_found = {
        'type': None,
        'redirect_url': base_url
    }

    path_arguments = request.path.split('/')[1:]

    if path_arguments and path_arguments[0].isdigit():
        try:
            from communities.models import Community
            c = Community.objects.get(pk=path_arguments[0])

            if path_arguments[1] == 'issues':
                not_found['type'] = 'no_issue'
                not_found['redirect_url'] = base_url + '/' + str(c.pk) + '/issues/'

                if path_arguments[2] == 'procedures':
                    not_found['type'] = 'no_procedure'
                    not_found['redirect_url'] = base_url + '/' + str(c.pk) + '/issues/procedures/'

            else:
                not_found['type'] = 'no_community_route'
                not_found['redirect_url'] = base_url + '/' + str(c.pk) + '/'

        except Community.DoesNotExist:
            not_found['type'] = 'no_community'

    return {'not_found': not_found}
