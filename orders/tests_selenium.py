from django.urls import reverse

from time import sleep

from .models import OrderInfo
from .tests import CheckoutConstants

from delivery.tests_selenium import DeliveryFirefoxTests
from menu.tests import MenuTestConstants


class OrdersFirefoxTests(MenuTestConstants, DeliveryFirefoxTests):

    CHECKOUT_URL = reverse('orders:checkout')


class ShoppingCartTests(OrdersFirefoxTests):

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

    def test_shopping_cart_has_items(self):
        """
        Added to cart items are displayed correctly.
        """
        self.login_browser_user()
        expected_contents = self.fill_session_cart()
        url = self.live_server_url + reverse('orders:shopping_cart')
        self.browser.get(url)

        list_items = self.browser.find_elements_by_tag_name('li')

        self.assertTrue(len(expected_contents) == len(list_items))

        for item, list_item in zip(expected_contents, list_items):
            text = list_item.text
            self.assertIn(item['name'], text)
            self.assertIn(str(item['price']), text)
            self.assertIn(str(item['cost']), text)
            amount = list_item.find_element_by_id('amount')
            self.assertEqual(item['amount'], int(amount.get_property('value')))
        self.assertIn(
            str(self.client.session['cart_cost']),
            self.browser.find_element_by_id('food_cost').text
        )

    def not_test_update_shopping_cart(self):
        """
        Amount of items in cart can be changed.
        """
        # TODO

    def not_test_remove_item_from_cart(self):
        """
        Items in cart can be removed.
        """
        # TODO

    def test_link_to_checkout(self):
        """
        Link at the bottom leads to checkout page.
        """
        self.login_browser_user()
        self.fill_session_cart()
        url = self.live_server_url + reverse('orders:shopping_cart')
        self.browser.get(url)
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
