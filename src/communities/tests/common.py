from collections import namedtuple

from django.contrib.auth import get_user_model

from communities.models import Community
from acl.default_roles import DefaultGroups
from users.models import OCUser

PASSWORD = 'secret'

User = get_user_model()


def create_community(community_name="Foo Inc.", committee_names=('Committee 1', 'Committee 2', 'Committee 3')):

    community = Community.objects.create(name=community_name)
    committees = []
    for name in committee_names:
        committees.append(community.committees.create(name=name, slug=name.lower().replace(" ", "_")))

    return community, committees


def create_users(community, n,  email_template=None):
    if not email_template:
        words = community.name.lower().split(" ,-_.")
        email_template = words[0] + "%d@" + ".".join(words)

    users = []
    for i in range(n):
        u = OCUser.objects.create_user(email_template % i,
                                       "%s %d" % (community.name, i + 1),
                                       password="password")
        community.community_memberships.create(user=u)
        users.append(u)
    return users

#
#
# def create_sample_community():
#     return create_community(roles=(
#         [DefaultGroups.CHAIRMAN] +
#         [DefaultGroups.SECRETARY] * 2 +
#         [DefaultGroups.BOARD] * 5 +
#         [DefaultGroups.MEMBER] * 10))
#

# class CommunitiesTestMixin(object):
#     @classmethod
#     def create_member(cls, username, community=None):
#         u = User.objects.create_user(
#             '{}@gmail.com'.format(username), username.title(), PASSWORD)
#         if community:
#             Membership.objects.create(community=community, user=u,
#                                       default_group_name=DefaultGroups.MEMBER)
#         return u
#
#     @classmethod
#     def setUpClass(cls):
#         super(CommunitiesTestMixin, cls).setUpClass()
#         cls.c1 = Community.objects.create(name='Public Community XYZZY',
#                                           is_public=True)
#         cls.c2 = Community.objects.create(name='Private Community ABCDE',
#                                           is_public=False)
#
#         cls.not_a_member = cls.create_member("foo")
#         cls.c1member = cls.create_member("bar", cls.c1)
#         cls.c2member = cls.create_member("baz", cls.c2)
#
#     @classmethod
#     def tearDownClass(cls):
#         Membership.objects.all().delete()
#         Community.objects.all().delete()
#         User.objects.all().delete()
#         super(CommunitiesTestMixin, cls).tearDownClass()
#
#     def visit(self, url, user=None, success=True):
#         client = self.client_class()
#         if user:
#             client.login(email=user.email, password=PASSWORD)
#         response = client.get(url)
#         self.assertEqual(response.status_code,
#                          200 if success else (403 if user else 302))
#         return response
