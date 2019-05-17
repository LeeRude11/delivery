from selenium import webdriver, common
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from django.urls import reverse


class FirefoxAccountsTests(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.close()


"""
Base HTML template to be used on every page contains these links.
"""
# TODO profile and stuff
# TODO index button on a logo
SITE_LINKS = [
    'menu:menu', 'delivery', 'info', 'orders:shopping_cart'
]
GUEST_LINKS = [
    'accounts:register', 'accounts:login'
]
USER_LINKS = [
    'accounts:profile', 'accounts:logout'
]


class DeliveryTest(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        url = self.live_server_url
        self.browser.get(url)

    def assert_links(self, links_list, should_exist=True):
        """
        Assert that links are present on the page.
        """
        for path in links_list:
            url = reverse(path)
            # TODO - kinda messy
            try:
                self.browser.find_element_by_xpath(f"//a[@href='{url}']")
            except(common.exceptions.NoSuchElementException):
                if should_exist:
                    raise AssertionError
            else:
                if not should_exist:
                    raise AssertionError

    def test_links_available(self):
        """
        A set of pages is available at the top of each of those pages.
        """
        self.assert_links(SITE_LINKS)

        # TODO - basic links belong in a dedicated <nav> element

    def test_guest_links_set(self):
        """
        Guests see links to /register and /login.
        And don't see /profile and /logout.
        """
        self.assert_links(GUEST_LINKS)
        self.assert_links(USER_LINKS, should_exist=False)

    def test_authorized_links_set(self):
        """
        Users see /profile and /logout.
        And don't see links to /register and /login.
        """
        self.assert_links(GUEST_LINKS)
        self.assert_links(USER_LINKS, should_exist=False)
