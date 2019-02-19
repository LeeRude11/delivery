from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

# from menu.models import MenuItem


class MenuDetailTests(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.close()

    def test_no_items_in_menu(self):
        """
        Accessing empty menu displays appropriate text.
        """
        menu_url = self.live_server_url + reverse('menu:menu')
        self.browser.get(menu_url)
        # TODO does find_element raises Exception if more than one found?
        self.assertEqual(
            self.browser.find_element_by_tag_name('li').text,
            "No items in menu :("
        )
