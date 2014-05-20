from communities.models import Community
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from issues.models import Issue, Proposal
from haystack.query import SearchQuerySet

User = get_user_model()


class IssuesTest(TestCase):
    def setUp(self):
        self.c = Community.objects.create(name="TEST COMMUNITY")
        self.u = User.objects.create(email="testuser@foo.com")

    def test_issue_comments(self):
        i = Issue.objects.create(community=self.c,
                                 title="Test",
                                 created_by=self.u)

        c = i.comments.create(content="foo", created_by=self.u)

    def test_issue_proposals(self):
        i = Issue.objects.create(community=self.c,
                                 title="Test",
                                 created_by=self.u)

        p = Proposal.objects.create(issue=i, created_by=self.u,
                                    type=Proposal.types.ADMIN, title="Foo",
                                    content="Foo foo foo")

        self.assertEquals(1, len(i.proposals.open()))
        self.assertEquals(0, len(i.proposals.closed()))
