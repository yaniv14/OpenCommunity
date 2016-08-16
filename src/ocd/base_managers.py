from django.db import models
from django.db.models.query import QuerySet
from haystack.query import SearchQuerySet
from acl.default_roles import DefaultGroups
from users.permissions import get_committee_perms, has_committee_perm


class ActiveQuerySetMixin(object):
    """Exposes methods that can be used on both the manager and the queryset.

    This allows us to chain custom methods.

    """

    def active(self):
        return self.get_queryset().filter(active=True)


class ConfidentialQuerySetMixin(object):
    """Exposes methods that can be used on both the manager and the queryset.

    This allows us to chain custom methods.

    """

    def object_access_control(self, user=None, committee=None):

        if not user or not committee:
            raise ValueError('The object access control method requires '
                             'both a user and a community object.')

        if hasattr(user, '_is_mock') and user._is_mock is True:
            return self.filter(is_confidential=False)

        elif user.is_superuser:
            return self.all()

        elif user.is_anonymous():
            return self.filter(is_confidential=False)

        else:
            if 'view_confidential' in get_committee_perms(user, committee):
                return self.all()
            else:
                return self.filter(is_confidential=False)


class ConfidentialQuerySet(QuerySet, ConfidentialQuerySetMixin):
    pass


class ConfidentialManager(models.Manager, ConfidentialQuerySetMixin):
    def get_queryset(self):
        return ConfidentialQuerySet(self.model, using=self._db)


class ConfidentialSearchQuerySet(SearchQuerySet):
    def object_access_control(self, user=None, committee=None, **kwargs):
        if not user or not committee:
            raise ValueError('The access validator requires both a user and '
                             'a committee object.')
        qs = self._clone()
        if user.is_superuser:
            return qs
        elif user.is_anonymous():
            return qs.filter(is_confidential=False)
        else:
            if not has_committee_perm(user, committee, 'view_confidential'):
                return qs.filter(is_confidential=False)
        return qs
