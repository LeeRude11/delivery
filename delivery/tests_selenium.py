from django.urls import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver, common

from time import sleep

from accounts.helpers import LoginBrowserUserMixin


class DeliveryFirefoxTests(LoginBrowserUserMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.close()

    def verify_available_fields(self, ids_list):
        """
        With a list of passed elements,
        verify that corresponding input elements are present on the page.
        """
        for field_name in ids_list:
            # django fields ids are formatted "id=id_{field_name}"
            field_id = 'id_' + field_name
            self.assertEqual(
                len(self.browser.find_elements_by_id(field_id)), 1
            )

    def fill_submit_form_with_values(self, form, values):
        """
        Fill a passed form with values from a dictionary,
        finding fields using its keys, and submit it.
        """
        for key, value in values.items():
            field = form.find_element_by_id('id_' + key)
            field.clear()
            # TODO can't pass datetime as is
            field.send_keys(str(value))
        form.submit()
        sleep(0.5)


"""
Base HTML template to be used on every page contains these links.
"""
# TODO index button on a logo
MAIN_ELEM = {'nav': 'main-bar'}
CART_ELEM = {'div': 'cart'}
SITE_LINKS = {
    'element': MAIN_ELEM,
    'links': ['index', 'menu:menu', 'delivery', 'info']
}
CART_LINKS = {
    'element': CART_ELEM,
    'links': ['orders:shopping_cart']
}
GUEST_LINKS = {
    'element': CART_ELEM,
    'links': ['accounts:register', 'accounts:login']
}
USER_LINKS = {
    'element': CART_ELEM,
    'links': ['accounts:profile', 'accounts:logout']
}


class DeliveryTests(DeliveryFirefoxTests):

    def setUp(self):
        super().setUp()
        url = self.live_server_url
        self.browser.get(url)

    """
    Helper functions.
    """

    def assert_links(self, links_dict, should_exist=True):
        """
        Assert that links are present in the element on the page.
        """
        (tag, id), = links_dict['element'].items()
        element = self.browser.find_element_by_id(id)
        self.assertEqual(element.tag_name, tag)

        if should_exist:
            check_function = self.link_exists
        else:
            check_function = self.link_does_not_exist

        for path in links_dict['links']:
            url = reverse(path)
            check_function(element, url)

    def link_exists(self, element, url):
        try:
            element.find_element_by_xpath(f"//a[@href='{url}']")
        except(common.exceptions.NoSuchElementException):
            raise AssertionError

    def link_does_not_exist(self, element, url):
        self.assertRaises(
            common.exceptions.NoSuchElementException,
            element.find_element_by_xpath,
            f"//a[@href='{url}']")

    """
    Tests.
    """

    def test_links_available(self):
        """
        A set of pages is available at the top of each of those pages.
        """
        self.assert_links(SITE_LINKS)
        self.assert_links(CART_LINKS)

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
        self.login_browser_user()
        self.browser.get(self.live_server_url)

        self.assert_links(GUEST_LINKS, should_exist=False)
        self.assert_links(USER_LINKS)


class DeliverySiteWideTests(DeliveryFirefoxTests):

    def test_messages_displayed(self):
        """
        Check that messages are displayed on the page.
        """
        url = reverse('orders:checkout')
        self.browser.get(self.live_server_url + url)
        messages = self.browser.find_element_by_class_name('messages')
        self.assertEqual(messages.tag_name, 'ul')
        error = messages.find_element_by_class_name('error')
        self.assertEqual(error.text, "Your cart is empty.")
