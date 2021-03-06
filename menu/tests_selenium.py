from django.urls import reverse

from random import randint
from time import sleep
from functools import partial
from selenium.common.exceptions import ElementClickInterceptedException

from .models import MenuItem
from .tests import MenuTestConstants
from core.tests_selenium import DeliveryFirefoxTests


class MenuListTests(DeliveryFirefoxTests):

    MENU_LIST_ID = 'menu-items-list'

    def test_no_items_in_menu(self):
        """
        Accessing empty menu displays appropriate text.
        """
        menu_url = self.live_server_url + reverse('menu:menu')
        self.browser.get(menu_url)
        menu_list = self.browser.find_element_by_id(self.MENU_LIST_ID)
        menu_items = menu_list.find_elements_by_tag_name('li')
        self.assertEqual(len(menu_items), 1)
        self.assertEqual(
            menu_items[0].text,
            "No items in menu :("
        )

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
            self.assertIn(
                item.name.casefold(),
                text.casefold()
            )
            self.assertIn(
                str(item.price),
                text
            )


class MenuDetailTests(DeliveryFirefoxTests):

    def test_detail_page_has_name_price(self):
        """
        Detail page of item has its name and price.
        """
        test_item = MenuItem.objects.create(
            name=f'Dish{randint(1, 10)}', price=randint(10, 300))

        url = self.live_server_url + reverse(
            'menu:detail', args=(test_item.id,))
        self.browser.get(url)

        name_header = self.browser.find_element_by_class_name('menu-item-name')
        price_header = self.browser.find_element_by_class_name(
            'menu-item-price')
        self.assertEqual(
            name_header.text.casefold(), test_item.name.casefold())
        self.assertIn(str(test_item.price), price_header.text)


# class MenuDetailTestsLoggedIn(MenuDetailTests):
class MenuDetailTestsLoggedIn():
    """
    Rerun those tests but with a logged in user.
    """
    # TODO unite tests to logged in

    def setUp(self):
        super().setUp()
        self.login_browser_user()


class DetailUpdateCartJS(DeliveryFirefoxTests):
    """
    Test JavaScript implementation of updating the user cart.
    """

    def return_url(self):
        return self.live_server_url + reverse(
            'menu:detail', args=(MenuItem.objects.get().id,))

    def setUp(self):
        super().setUp()
        MenuItem.objects.create(
            name=f'Dish{randint(1, 10)}', price=randint(10, 300))

        self.url = self.return_url()
        self.browser.get(self.url)

        self.current_amount = self.browser.find_element_by_class_name(
            'current-amount')
        self.actions = {}

        ch_amount = self.browser.find_elements_by_class_name('change-amount')
        increase_buttons = []
        for button in ch_amount:
            action = button.get_attribute('data-action')
            if action == 'increase':
                increase_buttons.append(button)
            else:
                self.actions[action] = button.click
        self.actions['increase'] = partial(
            self.increase_click,
            increase_buttons
        )

    def increase_click(self, buttons):
        """
        If amount is zero, a cover element increases it to 1.
        """
        try:
            buttons[0].click()
        except(ElementClickInterceptedException):
            buttons[1].click()

    def assert_no_errors(self):
        error_div = self.browser.find_elements_by_id('error-div')
        self.assertEqual(len(error_div), 0)

    def test_change_amount(self):
        """
        Clicking on 'increase' and 'decrease' elements changes the amount
        accordingly.
        """

        for i in range(10):
            self.assertEqual(int(self.current_amount.text), i)
            self.actions['increase']()

        for i in range(10, 0, -1):
            self.assertEqual(int(self.current_amount.text), i)
            self.actions['decrease']()
        self.assertEqual(int(self.current_amount.text), 0)
        self.assert_no_errors()

    def test_cart_cost_updated(self):
        """
        Test that with amount update cart cost is updated as well.
        """
        cart_cost = self.browser.find_element_by_id('cart-cost')

        self.assertEqual(
            int(cart_cost.text),
            0
        )

        for i in range(1, 11):
            self.actions['increase']()
            sleep(0.1)
            self.assertEqual(
                int(cart_cost.text), i * MenuItem.objects.get().price)
        self.assert_no_errors()


class ListRerunUpdateCartJS(DetailUpdateCartJS):
    """
    Rerun in List view.
    """

    def return_url(self):
        """
        Overwrite to reverse menu list url.
        """
        return self.live_server_url + reverse('menu:menu')


class ListUpdateCartJS(MenuTestConstants, DeliveryFirefoxTests):
    """
    List tests with a list of items.
    """

    def setUp(self):
        super().setUp()
        for i in range(3):
            MenuItem.objects.create(
                name=f'Dish{i}', price=randint(10, 300))
        self.menu_items = MenuItem.objects.all()

        url = self.live_server_url + reverse('menu:menu')
        self.browser.get(url)

    def test_distinct_items(self):
        """
        List items are attached to corresponding items.
        """
        cart_cost_div = self.browser.find_element_by_id('cart-cost')

        expected_cart_cost = 0
        for i, item in enumerate(self.menu_items):
            current_item = self.browser.find_elements_by_class_name(
                'menu-item')[i]
            current_amount = current_item.find_element_by_class_name(
                'current-amount')
            self.assertEqual(current_amount.text, '0')
            self.assertEqual(
                current_amount.get_attribute('data-item_id'),
                str(item.id))

            rand_clicks = randint(1, 5)
            for i in range(rand_clicks):
                increase_buttons = current_item.find_elements_by_xpath(
                    ".//div[@data-action='increase']")
                try:
                    increase_buttons[0].click()
                except(ElementClickInterceptedException):
                    increase_buttons[1].click()

            self.assertEqual(current_amount.text, str(rand_clicks))

            expected_cart_cost += item.price * rand_clicks

            self.assertEqual(
                expected_cart_cost,
                int(cart_cost_div.text))
