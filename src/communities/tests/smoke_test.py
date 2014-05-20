from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from communities.tests.common import CommunitiesTestMixin


class CommunitiesTest(CommunitiesTestMixin, TestCase):
    def visit_home(self, user=None):
        response = self.visit(reverse('home'), user)
        self.assertContains(response, self.c1.name)
        return response

    def visit_community(self, community, *args, **kwargs):
        return self.visit(community.get_absolute_url(), *args, **kwargs)

    def test_homepage_anonymous(self):
        response = self.visit_home()
        self.assertNotContains(response, self.c2.name)

    def test_homepage_member(self):
        response = self.visit_home(self.c2member)
        self.assertContains(response, self.c2.name)

    def test_homepage_not_a_member(self):
        response = self.visit_home(self.not_a_member)
        self.assertNotContains(response, self.c2.name)

    def test_visit_community_public_anonymous(self):
        response = self.visit_community(self.c1)

    def test_visit_community_public_logged_in(self):
        response = self.visit_community(self.c1, self.c2member)

    def test_visit_community_public_member(self):
        response = self.visit_community(self.c1, self.c1member)

    def test_visit_community_private_anonymous(self):
        response = self.visit_community(self.c2, success=False)

    def test_visit_community_private_logged_in(self):
        response = self.visit_community(self.c2, self.c1member, success=False)

    def test_visit_community_private_member(self):
        response = self.visit_community(self.c2, self.c2member)

