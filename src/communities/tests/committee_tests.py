from communities.models import Community
from communities.tests.common import create_community, create_users
from django.test.testcases import TestCase
from users.models import OCUser


class CommitteeTests(TestCase):
    def setUp(self):
        self.c, self.committees = create_community()
        self.users = create_users(self.c, 10)
        assert isinstance(self.c, Community)

    def visit(self, url, user=None, success=True):
        client = self.client_class()
        if user:
            client.force_login(user)
        response = client.get(url)
        self.assertEqual(response.status_code,
                         200 if success else (403 if user else 302))
        return response

    def test_commiteee_permssions(self):
        self.assertEqual(self.c.committees.count(), 4)
        non_community_user = OCUser.objects.create_user("foo123@bar.com")
        user = self.users[0]
        assert isinstance(user, OCUser)

        url = self.c.get_absolute_url()
        self.visit(url, success=False)
        self.visit(url, user=non_community_user, success=False)
        self.visit(url, user=user)

        committee = self.c.committees.first()
        url = committee.get_absolute_url()
        self.visit(url, success=False)
        self.visit(url, user=non_community_user, success=False)
        self.visit(url, user=user, success=False)

        mem = user.committee_memberships.create(
            committee=committee,
            role=self.c.roles.first(),
        )

        self.visit(url, user=user)

    def test_commiteee_group_permssions(self):
        user = self.users[0]
        assert isinstance(user, OCUser)
        committee = self.c.committees.first()
        url = committee.get_absolute_url()
        self.visit(url, user=user, success=False)

        group2 = self.c.groups.first()

        group1 = self.c.groups.create(title="dummy")


        gu = user.group_users.create(group=group1)

        self.visit(url, user=user, success=False)

        gu = user.group_users.create(group=group2)
        self.visit(url, user=user)


        # def test_create_meeting(self):
        #     self.issues = [
        #         self.c.issues.create(
        #             created_by=self.chair[0],
        #             status=IssueStatus.IN_UPCOMING_MEETING,
        #             order_in_upcoming_meeting=i + 1,
        #
        #         ) for i in xrange(20)
        #     ]
        #
        #     self.assertEquals(20, self.c.upcoming_issues().count())
        #
        #     self.c.upcoming_meeting_participants.add(self.members[-1])
        #     self.c.upcoming_meeting_participants.add(self.members[-2])
        #     self.c.upcoming_meeting_participants.add(self.members[-3])
        #     self.c.upcoming_meeting_participants.add(self.chair[0])
        #
        #     m = Meeting(held_at=timezone.now())
        #     self.c.close_meeting(m, self.chair[0], self.c)
        #
        #     self.assertEquals(20, m.agenda_items.count())
        #     self.assertEquals(4, m.participations.filter(is_absent=False).count())
        #     self.assertEquals(7, m.participations.filter(is_absent=True).count())
