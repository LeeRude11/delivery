from django.urls import reverse

from random import randint
from time import sleep

from .models import MenuItem
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

        name_header = self.browser.find_element_by_class_name('item-name')
        price_header = self.browser.find_element_by_class_name('item-price')

        self.assertEqual(name_header.text, test_item.name)
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


class MenuUpdateCartJS(DeliveryFirefoxTests):
    """
    Test JavaScript implementation of updating the user cart.
    """

    def setUp(self):
        super().setUp()

        new_menu_item = MenuItem.objects.create(
            name=f'Dish{randint(1, 10)}', price=randint(10, 300))

        self.url = self.live_server_url + reverse(
            'menu:detail', args=(new_menu_item.id,))
        self.browser.get(self.url)

        self.current_amount = self.browser.find_element_by_class_name(
            'current-amount')
        self.actions = {}

        ch_amount = self.browser.find_elements_by_class_name('change-amount')
        for button in ch_amount:
            action = button.get_attribute('data-action')
            self.actions[action] = button

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
            self.actions['increase'].click()

        for i in range(10, 0, -1):
            self.assertEqual(int(self.current_amount.text), i)
            self.actions['decrease'].click()
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
            self.actions['increase'].click()
            sleep(0.1)
            self.assertEqual(
                int(cart_cost.text), i * MenuItem.objects.get().price)
        self.assert_no_errors()
