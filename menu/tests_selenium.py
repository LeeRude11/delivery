from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from random import randint

from menu.models import MenuItem
# TODO common operations? reusable apps?
from orders.tests import create_new_user
from time import sleep


class FirefoxTests(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.close()

    def login_browser_user(self):
        """
        Create and login a test user.
        """
        # https://stackoverflow.com/a/22497239
        user = create_new_user()
        self.client.login(username=user.phone_number, password='testpassword')
        cookie = self.client.cookies['sessionid']
        self.browser.get(self.live_server_url + '/admin/')
        self.browser.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })


class MenuListTests(FirefoxTests):

    def test_no_items_in_menu(self):
        """
        Accessing empty menu displays appropriate text.
        """
        menu_url = self.live_server_url + reverse('menu:menu')
        self.browser.get(menu_url)
        # TODO does find_element raises Exception if more than one found?
        # TODO it doesn't - check that it's the only one
        self.assertEqual(
            self.browser.find_element_by_tag_name('li').text,
            "No items in menu :("
        )

    # driver.find_element_by_link_text('Continue')
    def test_item_appear_in_menu(self):
        """
        Created MenuItem-s appear on menu page.
        """

        for i in range(1, 4):
            MenuItem.objects.create(name=f'Dish{i}', price=randint(10, 300))

        menu_url = self.live_server_url + reverse('menu:menu')
        self.browser.get(menu_url)
        for item in MenuItem.objects.all():
            text = self.browser.find_element_by_xpath(
                f"//a[@href='{reverse('menu:detail', args=(item.id,))}']").text
            self.assertEqual(
                f'{item.name} - {item.price}',
                text
            )


class MenuDetailTests(FirefoxTests):

    def test_detail_page_has_name_price(self):
        """
        Detail page of item has its name and price.
        """
        test_item = MenuItem.objects.create(
            name=f'Dish{randint(1, 10)}', price=randint(10, 300))

        url = self.live_server_url + reverse(
            'menu:detail', args=(test_item.id,))
        self.browser.get(url)

        name_header = self.browser.find_element_by_id('item_name')
        price_header = self.browser.find_element_by_id('item_price')

        self.assertEqual(name_header.text, test_item.name)
        self.assertIn(str(test_item.price), price_header.text)

    def test_amount_accepted_and_updates(self):
        """
        Providing value in amount form updates current amount.
        """
        # self.login_browser_user()

        new_menu_item = MenuItem.objects.create(
            name=f'Dish{randint(1, 10)}', price=randint(10, 300))

        url = self.live_server_url + reverse(
            'menu:detail', args=(new_menu_item.id,))

        self.browser.get(url)
        amount_form = self.browser.find_element_by_id(
            'amount')

        self.assertEqual(
            int(amount_form.get_property('value')),
            0
        )

        amount = randint(1, 10)
        amount_form.clear()
        amount_form.send_keys(amount)
        amount_form.submit()

        sleep(0.5)
        self.browser.get(url)
        amount_form = self.browser.find_element_by_id(
            'amount')
        self.assertEqual(
            int(amount_form.get_property('value')),
            amount
        )


class MenuDetailTestsLoggedIn(MenuDetailTests):
    """
    Rerun those tests but with a logged in user.
    """
    def setUp(self):
        super().setUp()
        self.login_browser_user()
