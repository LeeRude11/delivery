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
            try:
                field.clear()
                field.send_keys(value)
            except(common.exceptions.InvalidElementStateException):
                # select dropdown date element
                date_field = webdriver.support.ui.Select(field)
                date_field.select_by_value(str(value))
        form.submit()
        sleep(0.5)

    def assert_element_stale(self, element):
        """
        Try to access an element expecting stale state.
        """
        self.assertRaises(
            common.exceptions.StaleElementReferenceException,
            element.is_enabled
        )

    def link_exists(self, element, url):
        try:
            link = element.find_element_by_xpath(f"//a[@href='{url}']")
        except(common.exceptions.NoSuchElementException):
            raise AssertionError
        return link


"""
Base HTML template to be used on every page contains these links.
"""
# TODO index button on a logo
NAV_ELEMENT = {
    'tag_name': 'nav',
    'id': 'main-bar'
}
NAV_LINKS = [
    {
        'tag_name': 'div',
        'id': 'main-sections',
        'links': [
            'core:index',
            'menu:specials',
            'menu:menu',
            'core:delivery',
            'core:info',
            'core:contacts'
        ]
    },
    {
        'tag_name': 'div',
        'id': 'user-sections',
        'links': [
            'orders:shopping_cart',
            'accounts:profile'
        ]
    }
]


class DeliveryTests(DeliveryFirefoxTests):

    def setUp(self):
        super().setUp()
        url = self.live_server_url
        self.browser.get(url)

    """
    Tests.
    """

    def test_header_displays_links(self):
        """
        All expected links are in header.
        """
        nav = self.browser.find_element_by_id(NAV_ELEMENT['id'])
        self.assertTrue(nav.tag_name, NAV_ELEMENT['tag_name'])

        for div in NAV_LINKS:
            found_div = nav.find_element_by_id(div['id'])
            self.assertTrue(found_div.tag_name, div['tag_name'])
            for link in div['links']:
                url = reverse(link)
                self.link_exists(found_div, url)


class DeliverySiteWideTests(DeliveryFirefoxTests):

    def test_messages_displayed(self):
        """
        Check that messages are displayed on the page in header.
        """
        url = reverse('orders:checkout')
        self.browser.get(self.live_server_url + url)
        header = self.browser.find_element_by_tag_name('header')
        messages = header.find_element_by_class_name('messages')
        self.assertEqual(messages.tag_name, 'ul')
        error = messages.find_element_by_class_name('error')
        self.assertEqual(error.text, "Your cart is empty.")
