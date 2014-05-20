from communities.models import Community
from django.test.testcases import TestCase

from communities.tests.common import create_sample_community
from django.utils import timezone
from issues.models import IssueStatus
from meetings.models import Meeting


class CreateMeetingTest(TestCase):
    def setUp(self):
        (self.c, self.members, self.chair) = create_sample_community()
        assert isinstance(self.c, Community)


    def test_create_meeting(self):
        self.issues = [
            self.c.issues.create(
                created_by=self.chair[0],
                status=IssueStatus.IN_UPCOMING_MEETING,
                order_in_upcoming_meeting=i + 1,

            ) for i in xrange(20)
        ]

        self.assertEquals(20, self.c.upcoming_issues().count())

        self.c.upcoming_meeting_participants.add(self.members[-1])
        self.c.upcoming_meeting_participants.add(self.members[-2])
        self.c.upcoming_meeting_participants.add(self.members[-3])
        self.c.upcoming_meeting_participants.add(self.chair[0])

        m = Meeting(held_at=timezone.now())
        self.c.close_meeting(m, self.chair[0])

        self.assertEquals(20, m.agenda_items.count())
        self.assertEquals(4, m.participations.filter(is_absent=False).count())
        self.assertEquals(7, m.participations.filter(is_absent=True).count())
