from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from random import randint
from datetime import datetime, timedelta

from .models import OrderInfo, OrderContents

from menu.models import MenuItem
from menu.tests import MenuTestConstants
from accounts.tests import AccountsTestConstants

USER_MODEL = get_user_model()


class OrderInfoTests(AccountsTestConstants, TestCase):

    def test_order_from_user(self):
        """Order is associated with user"""
        new_user = self.create_test_user()
        new_order = OrderInfo.objects.create(user=new_user)
        self.assertEqual(new_order.user, new_user)

    def test_order_cost_function(self):
        """OrderContents.cost is correctly added in total cost"""
        cost = 0
        order = OrderInfo.objects.create(user=self.create_test_user())
        for i in range(3):
            price = randint(1, 500)
            amount = randint(1, 10)
            cost += price * amount
            menu_item = MenuItem.objects.create(name=f'dish{i}', price=price)
            OrderContents.objects.create(
                order=order, menu_item=menu_item, amount=amount)
            self.assertEqual(cost, order.total_cost)

    def test_order_update_status_function(self):
        """Status is correctly updated"""
        order = OrderInfo.objects.create(user=self.create_test_user())
        self.assertIsInstance(order.ordered, datetime)
        self.assertIsNone(order.cooked)
        self.assertIsNone(order.delivered)

        order.update_current_state()
        self.assertIsInstance(order.cooked, datetime)
        self.assertIsNone(order.delivered)

        order.update_current_state()
        self.assertIsInstance(order.cooked, datetime)
        self.assertIsInstance(order.delivered, datetime)


"""View tests."""


class OrdersTestCase(AccountsTestConstants, MenuTestConstants, TestCase):

    # TODO - rerun test with login_test_user in SetUp and without by default
    SHOP_CART_URL = reverse('orders:shopping_cart')
    ORDERS_UPDATE = 'orders:orders_update_cart'
    SHOP_CART_PAGE = 'orders/shopping_cart.html'


class ShoppingCartViewTests(OrdersTestCase):

    URL = OrdersTestCase.SHOP_CART_URL

    def test_shopping_cart_is_empty(self):
        """
        Opening page with empty cart displays appropriate text.
        """
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your shopping cart is empty.")
        self.assertQuerysetEqual(response.context['contents'], [])

    def test_shopping_cart_not_empty(self):
        """
        Page has user's cart contents.
        """
        expected_contents = self.fill_session_cart()
        response = self.client.get(self.URL)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_shopping_cart_displays_total_cost(self):
        """
        Whole cart cost is correctly calculated and displayed.
        """
        expected_cart_cost = 0
        for item in self.fill_session_cart():
            expected_cart_cost += item['price'] * item['amount']

        self.client.get(self.URL)
        self.assertEqual(self.client.session['cart_cost'], expected_cart_cost)


class UpdateCartViewTests(OrdersTestCase):

    def test_update_shopping_cart(self):
        """
        Change amount of items from shopping cart page.
        """
        expected_contents = self.fill_session_cart()
        for item in expected_contents:
            update_url = reverse(self.ORDERS_UPDATE, args=(item['id'],))
            new_amount = randint(1, 10)
            self.client.post(update_url, {'amount': new_amount})
            item['amount'] = new_amount
            item['cost'] = new_amount * item['price']

        response = self.client.get(self.SHOP_CART_URL)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_remove_item_from_cart(self):
        """
        Setting amount to 0 removes item from cart page.
        """
        expected_contents = self.fill_session_cart()
        index = randint(0, 2)
        update_url = reverse(
            self.ORDERS_UPDATE, args=(expected_contents[index]['id'],))
        new_amount = 0
        self.client.post(update_url, {'amount': new_amount})

        expected_contents.pop(index)

        response = self.client.get(self.SHOP_CART_URL)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_update_order_menu_errors(self):
        """
        Error messages are sent from menu.views.update_cart,
        and returned page is orders.shopping_page.
        """
        item = self.fill_session_cart()[0]
        update_url = reverse(self.ORDERS_UPDATE, args=(item['id'],))
        new_amount = -1
        response = self.client.post(update_url, {'amount': new_amount},
                                    follow=True)

        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Incorrect amount." in message.message)
        self.assertFalse(self.client.session.modified)
        self.assertEqual(response.status_code, 200)
        # TODO template, eh?
        self.assertTemplateUsed(response, self.SHOP_CART_PAGE)


class RemoveItemViewTests(OrdersTestCase):

    def test_remove_item(self):
        """
        View removes item from cart.
        """
        expected_contents = self.fill_session_cart()
        index = randint(0, 2)
        update_url = reverse(
            'orders:remove_item', args=(expected_contents[index]['id'],))
        self.client.post(update_url)

        expected_contents.pop(index)

        response = self.client.get(self.SHOP_CART_URL)
        self.assertEqual(response.context['contents'], expected_contents)


class LoggedInTests(ShoppingCartViewTests,
                    UpdateCartViewTests, RemoveItemViewTests):
    """
    Rerun those suites with a logged in users.
    """
    # TODO - unite with Checkout logged in? Only URL is a problem
    def setUp(self):
        super().setUp()
        self.login_test_user()


class CheckoutConstants(object):

    CHECKOUT_FIELDS = [
        'phone_number',
        'first_name',
        'second_name',
        'email',
        'street',
        'house',
        'apartment'
    ]
    URL = reverse('orders:checkout')

    def build_checkout_form(self):
        return {
            field: self.user_for_tests[field] for field in self.CHECKOUT_FIELDS
        }


class CheckoutTestCase(CheckoutConstants, OrdersTestCase):
    """
    Pack two classes for two test suites.
    """


class CheckoutViewSpecificTests(CheckoutTestCase):

    """
    Tests that are only run as guest or user.
    """
    def test_checkout_form_prefilled(self):
        """
        With a logged-in user, checkout form is prefilled with their info.
        """
        self.login_test_user()
        self.fill_session_cart()
        response = self.client.get(self.URL)
        form_fields_w_values = response.context['form'].initial
        self.assertEqual(len(form_fields_w_values.items()),
                         len(self.CHECKOUT_FIELDS))
        for k, v in form_fields_w_values.items():
            self.assertEqual(v, self.user_for_tests[k])

    def test_user_info_updated(self):
        """
        If user provides info different from prefilled, his info is updated.
        """
        self.login_test_user()
        self.fill_session_cart()
        response = self.client.get(self.URL)
        form_fields_w_values = response.context['form'].initial
        for field in form_fields_w_values:
            form_fields_w_values[field] += "1"

        self.client.post(self.URL, form_fields_w_values, follow=True)
        user = USER_MODEL.objects.get()
        for field, value in form_fields_w_values.items():
            user_value = getattr(user, field)
            self.assertEqual(user_value, value)

    def test_guest_user_created(self):
        """
        When anonymous user posts an order,
        a corresponding guest user is created.
        """
        self.assertFalse(USER_MODEL.objects.all().exists())
        self.fill_session_cart()
        self.client.post(self.URL, self.build_checkout_form())
        self.assertTrue(USER_MODEL.objects.get().is_guest)


class CheckoutViewTests(CheckoutTestCase):

    """
    General tests, which are first run as guest.
    """
    def test_can_not_access_checkout_with_empty_cart(self):
        """
        Trying to access checkout page whether via GET or POST request
        with an empty cart redirects to shopping cart page.
        """
        responses = [self.client.post(self.URL, follow=True),
                     self.client.get(self.URL, follow=True)]

        for response in responses:
            self.assertRedirects(response, reverse('orders:shopping_cart'))
            message = list(response.context.get('messages'))[0]
            self.assertEqual(message.tags, 'error')
            self.assertTrue("Your cart is empty." in message.message)

    def test_can_access_checkout(self):
        """
        Users with non-empty cart can access checkout page.
        """
        self.fill_session_cart()
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/checkout.html')

    def test_checkout_renders_form(self):
        """
        Checkout page renders a form with expected fields.
        """
        self.fill_session_cart()
        response = self.client.get(self.URL)
        rendered_fields = list(response.context['form'].fields.keys())
        for field in self.CHECKOUT_FIELDS:
            rendered_fields.remove(field)
        self.assertEqual(len(rendered_fields), 0)

    def test_process_order(self):
        """
        Order is successfully transferred from Session to database.
        """
        expected_contents = self.fill_session_cart()

        response = self.client.post(self.URL, self.build_checkout_form())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your order was placed.")

        placed_order = OrderInfo.objects.get()
        order_contents = placed_order.ordercontents_set.all()
        # arbitrary 5 seconds to account for some fault
        self.assertTrue(
            timezone.now() - placed_order.ordered < timedelta(seconds=5))
        self.assertEqual(len(expected_contents), len(order_contents))
        for expected in expected_contents:
            db_contents = order_contents.get(menu_item__id=expected['id'])
            dict_from_db = {
                'id': db_contents.menu_item.id,
                'name': db_contents.menu_item.name,
                'price': db_contents.menu_item.price,
                'amount': db_contents.amount,
                'cost': db_contents.cost,
            }
            self.assertEqual(expected, dict_from_db)

    def test_cart_flushed(self):
        """
        On successful order, Session cart is emptied.
        """
        self.fill_session_cart()

        session = self.client.session
        self.assertNotEqual(session['cart'], {})
        self.assertNotEqual(session['cart_cost'], 0)

        self.client.post(self.URL, self.build_checkout_form())

        session = self.client.session
        self.assertEqual(session['cart'], {})
        self.assertEqual(session['cart_cost'], 0)

    def test_order_by_user(self):
        """
        Order is associated with a user or guest that posted it.
        """
        self.fill_session_cart()
        self.client.post(self.URL, self.build_checkout_form())
        self.assertEqual(OrderInfo.objects.get().user,
                         USER_MODEL.objects.get())


class CheckoutViewLoggedTests(CheckoutViewTests):

    """
    Rerun with a logged in user.
    """
    def setUp(self):
        super().setUp()
        self.login_test_user()
