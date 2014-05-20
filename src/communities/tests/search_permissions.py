import logging
from django.contrib.auth import get_user_model

from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.testcases import TestCase
from users.default_roles import DefaultGroups
from users.models import Membership

User = get_user_model()

from communities.models import Community


class CommunitiesTest(TestCase):
    def setUp(self):
        self.c1 = Community.objects.create(name='Public Community XYZZY', is_public=True)
        self.c2 = Community.objects.create(name='Private Community ABCDE', is_public=False)
        self.assertEquals(2, Community.objects.count())

        self.not_a_member = User.objects.create_user('foo@gmail.com', 'Foo', 'secret')
        self.c2member = User.objects.create_user('bar@gmail.com', 'Bar', 'secret')
        Membership.objects.create(community=self.c2, user=self.c2member, default_group_name=DefaultGroups.MEMBER)

        self.client = Client()


    def tearDown(self):
        pass


    def test_search_annonymous_public(self):
        response = self.client.get(reverse('community_search',kwargs={'pk':self.c1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_search_annonymous_private(self):
        response = self.client.get(reverse('community_search',kwargs={'pk':self.c2.pk}))
        self.assertEqual(response.status_code, 302)

    def test_search_member_public(self):
        self.client.login(email=self.c2member.email, password='secret')
        response = self.client.get(reverse('community_search',kwargs={'pk':self.c1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_search_member_private(self):
        self.client.login(email=self.c2member.email, password='secret')
        response = self.client.get(reverse('community_search',kwargs={'pk':self.c2.pk}))
        self.assertEqual(response.status_code, 200)

    def test_search_not_a_member_public(self):
        self.client.login(email=self.not_a_member.email, password='secret')
        response = self.client.get(reverse('community_search',kwargs={'pk':self.c1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_search_not_a_member_private(self):
        self.client.login(email=self.not_a_member.email, password='secret')
        response = self.client.get(reverse('community_search',kwargs={'pk':self.c2.pk}))
        self.assertEqual(response.status_code, 403)
