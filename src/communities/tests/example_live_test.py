from __future__ import unicode_literals

import urlparse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.urlresolvers import reverse
from selenium.webdriver.firefox.webdriver import WebDriver

from communities.models import Community
from users.models import OCUser


class ExampleCommunityLiveTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super(ExampleCommunityLiveTests, cls).setUpClass()
        cls.selenium = WebDriver()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(ExampleCommunityLiveTests, cls).tearDownClass()

    def setUp(self):
        self.community = Community.objects.create(
            name = "Kibbutz Broken Dream",
        )
        alon = "Alon"
        self.u1 = OCUser.objects.create_superuser("alon@dream.org", alon, "secret")

    def full_url(self, s):
        return self.live_server_url + s

    def get_current_path(self):
        return urlparse.urlsplit(self.selenium.current_url).path

    def assert_current_path(self, path):
        self.assertEqual(path, self.get_current_path())

    def test_login(self):
        url = self.full_url(self.community.get_absolute_url())
        # from IPython import embed
        # embed()

        login_url = self.full_url(reverse("login"))
        self.selenium.get(login_url)
        self.assert_current_path(reverse('login'))
        username_input = self.selenium.find_element_by_id("id_username")
        username_input.send_keys(self.u1.email)
        password_input = self.selenium.find_element_by_id("id_password")
        password_input.send_keys('secret')
        # raw_input()
        self.selenium.find_element_by_xpath('//input[@type="submit"]').click()
        # raw_input()


        self.selenium.get(url)
        # raw_input()

        # self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()        self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
        # username_input = self.selenium.find_element_by_name("username")
        # username_input.send_keys('myuser')
        # password_input = self.selenium.find_element_by_name("password")
        # password_input.send_keys('secret')
        # self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()