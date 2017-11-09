from acl.default_roles import ALL_PERMISSIONS
from communities.models import Committee

"""
These functions work with anonymous users as well, and therefore are not a
part of the OCUser model.
"""


def load_community_permissions(user, community):
    from users.models import CommunityMembership
    if user.is_authenticated():
        try:
            all_perms = set()
            committees = Committee.objects.filter(community=community)
            for committee in committees:
                if committee.community_role:
                    all_perms.update(committee.community_role.all_perms())
            try:
                membership = CommunityMembership.objects.get(community=community, user=user)
            except CommunityMembership.DoesNotExist:
                membership = None
            if membership:
                if membership.is_manager:
                    all_perms.update(['invite_member', 'manage_communitygroups'])
            # Should be removed in future, all communities should have basic roles
            if user.community_memberships.filter(community=community).exists():
                all_perms.update(['access_community'])
            return all_perms
        except CommunityMembership.DoesNotExist:
            pass

    if community.is_public:
        # todo: some basic permissions for community?
        return set(['access_community'])

    return []


def load_committee_permissions(user, committee):
    if not user.is_authenticated():
        if committee.is_public:
            # todo: some basic permissions for committee?
            return set(['access_committee'])

        return set()

    all_perms = set()

    # Memberships roles
    membership = user.committee_memberships.filter(committee=committee).first()
    # if membership:
    #     all_perms.update(['access_committee'])
    role = membership.role if membership else committee.community_role
    if role:
        all_perms.update(role.all_perms())

    group_roles = committee.group_roles.filter(committee__community__groups__group_users__user=user)
    print(group_roles.query)
    print(group_roles)
    for group_role in group_roles:
        all_perms.update(group_role.role.all_perms())

    print(all_perms)

    return all_perms


def get_community_permissions(user, community, committee=None):
    """ returns a cached list of permissions for a community and a user """

    if not hasattr(user, '_community_permissions_cache'):
        user._community_permissions_cache = {}

    if community.id not in user._community_permissions_cache:
        perms = load_community_permissions(user, community)
        user._community_permissions_cache[community.id] = perms

    return user._community_permissions_cache[community.id]


def get_committee_permissions(user, committee):
    """ returns a cached list of permissions for a community and a user """

    if not hasattr(user, '_committee_permissions_cache'):
        user._committee_permissions_cache = {}

    if committee.id not in user._committee_permissions_cache:
        perms = load_committee_permissions(user, committee)
        user._committee_permissions_cache[committee.id] = perms

    return user._committee_permissions_cache[committee.id]


###################################

def has_community_perm(user, community, perm):
    if user.is_active and user.is_superuser:
        return True

    return perm in get_community_permissions(user, community)


def get_community_perms(user, community):
    if user.is_active and user.is_superuser:
        perms = ALL_PERMISSIONS
    else:
        perms = get_community_permissions(user, community)

    return perms


def has_committee_perm(user, committee, perm):
    if user.is_active and user.is_superuser:
        return True
    return perm in get_committee_permissions(user, committee)


def get_committee_perms(user, committee):
    if user.is_active and user.is_superuser:
        perms = ALL_PERMISSIONS
    else:
        perms = get_committee_permissions(user, committee)

    return perms
