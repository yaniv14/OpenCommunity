import urlparse
from communities.models import Community

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, resolve
from django.test.client import Client
from django.test.testcases import TestCase

from communities.tests.common import create_sample_community
from issues.models import Issue, Proposal, ProposalType
from users.models import Membership

User = get_user_model()


class IssuesUITest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.community, cls.members, cls.chairmen = create_sample_community()

    @classmethod
    def tearDownClass(cls):
        Membership.objects.all().delete()
        Community.objects.all().delete()
        User.objects.all().delete()

    def setUp(self):
        self.client = Client()

    def login_chairmen(self):
        self.client.login(username=self.chairmen[0].email,
                          password="password")


    def test_view_create_issue_unauthorized(self):
        self.client.login(email=self.members[-1].email, password='password')
        response = self.client.get(
            reverse('issue_create', args=(self.community.id,)))
        self.assertEquals(403, response.status_code)

    def test_view_create_issue(self):
        title = "Issue ABC"
        abstract = "Lorem Ipsum"

        self.assertEquals(0, Issue.objects.count())

        self.login_chairmen()
        url = reverse('issue_create', args=(self.community.id,))
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        response = self.client.post(url, {
            'proposal-type': '',
            'title': title,
            'abstract': abstract,
        })
        self.assertEquals(200, response.status_code)
        # Ajax call returns a url to redirect to.
        rurl = urlparse.urlparse(response.content).path
        m = resolve(rurl)
        self.assertEquals('issue', m.url_name)
        i = Issue.objects.get(**m.kwargs)
        self.assertEquals(i.title, title)
        self.assertEquals(i.abstract, abstract)


    def test_create_proposal(self):
        i = Issue(community=self.community, title="Issue ABC",
                  created_by=self.chairmen[0])
        i.full_clean()
        i.save()

        title = 'Proposal XYZ'
        content = 'hellow world'

        self.assertEquals(0, Proposal.objects.count())

        self.login_chairmen()
        url = reverse('proposal_create', args=(self.community.id, i.id))
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        response = self.client.post(url, {
            'proposal-type': ProposalType.RULE,
            'proposal-title': title,
            'proposal-content': content,
            'proposal-tags': 'tag1,tag2,tag3',
        })
        self.assertEquals(200, response.status_code)
        # Ajax call returns a partial html
        self.assertEquals(1, Proposal.objects.count())
        p = Proposal.objects.all()[0]
        assert isinstance(p, Proposal)
        self.assertContains(response, p.get_absolute_url())
        self.assertEquals(title, p.title)
        self.assertEquals(content, p.content)
