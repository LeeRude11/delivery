from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class FirefoxAccountsTests(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.close()


"""
Base HTML template to be used on every page contains these links.
"""
# TODO profile and stuff
SITE_LINKS = [
    'menu', 'delivery', 'shopping cart'
]


class DeliveryTest(FirefoxAccountsTests):

    def test_home_page(self):
        """
        A home page is available.
        """
        url = self.live_server_url
        self.browser.get(url)
        # TODO

    def not_test_links_available(self):
        """
        A set of pages is available at the top of each of those pages.
        """
        # TODO
