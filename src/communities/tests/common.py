from collections import namedtuple

from django.contrib.auth import get_user_model

from communities.models import Community
from users.default_roles import DefaultGroups
from users.models import OCUser, Membership

PASSWORD = 'secret'

User = get_user_model()


def create_community(roles, community_name="Foo Inc.", email_template=None):
    community = Community.objects.create(name="Foo Inc.")
    members = []
    chairmen = []
    if not email_template:
        words = community_name.lower().split(" ,-_.")
        email_template = words[0] + "%d@" + ".".join(words)
    for i, g in enumerate(roles):
        u = OCUser.objects.create_user(email_template % i,
                                       "%s %d" % (community_name, i),
                                       password="password")
        Membership.objects.create(user=u, community=community,
                                  default_group_name=g)
        if g == DefaultGroups.CHAIRMAN:
            chairmen.append(u)
        members.append(u)
    return namedtuple('Result', ['community', 'members', 'chairmen'])(
        community, members, chairmen)


def create_sample_community():
    return create_community(roles=(
        [DefaultGroups.CHAIRMAN] +
        [DefaultGroups.SECRETARY] * 2 +
        [DefaultGroups.BOARD] * 5 +
        [DefaultGroups.MEMBER] * 10))


class CommunitiesTestMixin(object):
    @classmethod
    def create_member(cls, username, community=None):
        u = User.objects.create_user(
            '{}@gmail.com'.format(username), username.title(), PASSWORD)
        if community:
            Membership.objects.create(community=community, user=u,
                                      default_group_name=DefaultGroups.MEMBER)
        return u

    @classmethod
    def setUpClass(cls):
        super(CommunitiesTestMixin, cls).setUpClass()
        cls.c1 = Community.objects.create(name='Public Community XYZZY',
                                          is_public=True)
        cls.c2 = Community.objects.create(name='Private Community ABCDE',
                                          is_public=False)

        cls.not_a_member = cls.create_member("foo")
        cls.c1member = cls.create_member("bar", cls.c1)
        cls.c2member = cls.create_member("baz", cls.c2)


    @classmethod
    def tearDownClass(cls):
        Membership.objects.all().delete()
        Community.objects.all().delete()
        User.objects.all().delete()
        super(CommunitiesTestMixin, cls).tearDownClass()


    def visit(self, url, user=None, success=True):
        client = self.client_class()
        if user:
            client.login(email=user.email, password=PASSWORD)
        response = client.get(url)
        self.assertEqual(response.status_code,
                         200 if success else (403 if user else 302))
        return response

