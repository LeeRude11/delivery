from django.urls import reverse

from random import randint
from time import sleep

from .models import OrderInfo
from .tests import CheckoutConstants

from core.tests_selenium import DeliveryFirefoxTests
from menu.tests import MenuTestConstants


class OrdersFirefoxTests(MenuTestConstants, DeliveryFirefoxTests):

    CHECKOUT_URL = reverse('orders:checkout')


class ShoppingCartTestsWithoutSetup(OrdersFirefoxTests):

    def test_shopping_cart_is_empty(self):
        """
        Empty shopping cart is displayed correctly.
        """
        self.login_browser_user()
        url = self.live_server_url + reverse('orders:shopping_cart')
        self.browser.get(url)

        self.assertEqual(
            self.browser.find_element_by_tag_name('p').text,
            "Your shopping cart is empty."
        )


class ShoppingCartTests(OrdersFirefoxTests):

    def setUp(self):
        super().setUp()
        self.login_browser_user()
        self.expected_contents = self.fill_session_cart()
        url = self.live_server_url + reverse('orders:shopping_cart')
        self.browser.get(url)

    def get_list_of_items(self):
        # TODO temporary solution
        body = self.browser.find_element_by_tag_name('main')
        return body.find_elements_by_tag_name('li')

    def get_item_dict(self, item):
        """
        Get actions and values associated with the item.
        """
        item_values = [
            'item-name', 'current-amount', 'item-price', 'item-cost']
        item_dict = {}
        for value in item_values:
            key = value.split('-')[1]
            item_dict[key] = item.find_element_by_class_name(value)
        item_dict['id'] = item_dict['amount'].get_attribute('data-item_id')

        ch_amount = item.find_elements_by_class_name('change-amount')
        for button in ch_amount:
            action = button.get_attribute('data-action')
            item_dict[action] = button

        return item_dict

    def test_shopping_cart_has_items(self):
        """
        Added to cart items are displayed correctly.
        """
        list_items = self.get_list_of_items()

        self.assertTrue(len(self.expected_contents) == len(list_items))

        for expected_item, list_item in zip(
                self.expected_contents, list_items):
            item_dict = self.get_item_dict(list_item)
            for key in expected_item:
                try:
                    list_value = item_dict[key].text
                except AttributeError:
                    list_value = item_dict[key]
                self.assertEqual(str(expected_item[key]), list_value)
        self.assertEqual(
            str(self.client.session['cart_cost']),
            self.browser.find_element_by_id('food-cost').text
        )

    def test_update_shopping_cart(self):
        """
        Amount of items in cart can be changed.
        """
        food_cost = self.browser.find_element_by_id('food-cost')
        old_food_cost = int(food_cost.text)

        items = self.get_list_of_items()
        index = randint(1, len(items) - 1)
        list_item = self.get_item_dict(items[index])
        item_price = self.expected_contents[index]['price']
        old_cost = self.expected_contents[index]['cost']

        increase_by = randint(5, 10)
        directions = [
            {
                'action': 'increase',
                'range': range(1, increase_by + 1)
            },
            {
                'action': 'decrease',
                'range': range(increase_by - 1, - 1, -1)
            }
        ]
        for direction in directions:
            for i in direction['range']:
                list_item[direction['action']].click()
                sleep(0.1)
                new_cost = int(list_item['cost'].text)
                new_food_cost = int(food_cost.text)
                self.assertTrue(new_food_cost - old_food_cost ==
                                new_cost - old_cost == item_price * i)

    def test_remove_item_from_cart(self):
        """
        Items in cart can be removed.
        """
        items = self.get_list_of_items()
        index = randint(1, len(items) - 1)
        list_item = self.get_item_dict(items[index])

        food_cost = self.browser.find_element_by_id('food-cost')
        old_food_cost = int(food_cost.text)
        cost_loss = self.expected_contents[index]['cost']
        list_item['remove'].click()

        new_food_cost = int(food_cost.text)
        self.assertEqual(new_food_cost, old_food_cost - cost_loss)
        self.assert_element_stale(items[index])

    def test_link_to_checkout(self):
        """
        Link at the bottom leads to checkout page.
        """
        self.browser.find_element_by_link_text('Checkout').click()
        self.assertEqual(self.browser.current_url,
                         self.live_server_url + self.CHECKOUT_URL)


class CheckoutTests(CheckoutConstants, OrdersFirefoxTests):

    def setUp(self):
        super().setUp()
        self.login_browser_user()
        self.fill_session_cart()
        url = self.live_server_url + self.CHECKOUT_URL
        self.browser.get(url)

    def get_checkout_form(self):
        """
        Return checkout form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_checkout_fields(self):
        """
        All expected fields are rendered.
        """

        checkout_fields = self.build_checkout_form().keys()

        self.verify_available_fields(checkout_fields)

    def test_checkout_fields_prefilled(self):
        """
        Checkout form is prefilled with user info if logged in.
        """
        checkout_fields = self.build_checkout_form()
        for name, value in checkout_fields.items():
            # django fields ids are formatted "id=id_{field_name}"
            field_id = 'id_' + name
            field = self.browser.find_element_by_id(field_id)
            self.assertEqual(
                field.get_attribute('value'), str(value)
            )

    def test_process_order(self):
        """
        Clicking on the button processes order.
        """
        checkout_form = self.get_checkout_form()
        checkout_form.submit()

        sleep(0.5)
        result = self.browser.find_element_by_id('result')
        self.assertIn(
            "Your order was placed.",
            result.text
        )
        self.assertTrue(len(self.client.session['cart']) == 0)
        OrderInfo.objects.get()

    def not_test_without_user(self):
        """
        Maybe rerun without users
        """
        # TODO
