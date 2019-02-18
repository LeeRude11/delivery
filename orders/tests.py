from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from random import randint
from datetime import datetime, timedelta

from .models import OrderInfo, OrderContents
from menu.models import MenuItem

DEF_NAME = 'New Dish'
DEF_PRICE = 100
ORDERS_UPDATE = 'orders:orders_update_cart'
SHOP_CART_PAGE = 'orders/shopping_cart.html'


def create_new_user():
    """Create a new user for tests"""
    return User.objects.create_user('testuser', None, 'testpassword')


def create_menu_item(name=DEF_NAME, price=DEF_PRICE):
    """
    Create and return a menu item with given name and price.
    """
    new_menu_item = MenuItem.objects.create(name=name, price=price)
    return new_menu_item


def create_new_user_and_return_his_order():
    return OrderInfo.objects.create(user=create_new_user())


class OrderInfoTests(TestCase):

    def test_order_from_user(self):
        """Order is associated with user"""
        new_user = create_new_user()
        new_order = OrderInfo.objects.create(user=new_user)
        self.assertEqual(new_order.user, User.objects.get(id=1))

    def test_order_cost_function(self):
        """OrderContents.cost is correctly added in total cost"""
        cost = 0
        order = create_new_user_and_return_his_order()
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
        order = create_new_user_and_return_his_order()
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


class CustomTestCase(TestCase):

    def assert_redirect_and_error_msg(
            self, path, redirect_to='accounts:login', get=True,
            msg_text="Must be logged in."):
        """
        Page redirects and shows an error message.
        Default is for a users-only page.
        Only accepts GET and POST requests
        """
        url = reverse(path)
        if get:
            response = self.client.get(url, follow=True)
        else:
            response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse(redirect_to))
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue(msg_text in message.message)

    def login_test_user(self):
        """
        Create and login a test user.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')

    def user_access_url(self, path):
        """
        Create and login a test user, then access passed path.
        """
        self.login_test_user()
        return reverse(path)

    def fill_session_cart(self):
        expected_contents = []
        for i in range(3):
            new_menu_item = create_menu_item(
                name=f'Dish{i}', price=randint(10, 300))
            add_url = reverse('menu:update_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            self.client.post(add_url, {'amount': amount})
            expected_contents.append({
                'id': new_menu_item.id,
                'name': new_menu_item.name,
                'price': new_menu_item.price,
                'amount': amount,
                'cost': new_menu_item.price * amount
            })
        return expected_contents


class ShoppingCartViewTests(CustomTestCase):

    def test_shopping_cart_redirects_anon_to_login(self):
        """
        TEMPORARY - unauthorized users can not access shopping cart page.
        """
        self.assert_redirect_and_error_msg(path='orders:shopping_cart')

    def test_shopping_cart_is_empty(self):
        """
        Opening page with empty cart displays appropriate text.
        """
        url = self.user_access_url('orders:shopping_cart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your shopping cart is empty.")
        self.assertQuerysetEqual(response.context['contents'], [])

    def test_shopping_cart_not_empty(self):
        """
        Page has user's cart contents.
        """
        url = self.user_access_url('orders:shopping_cart')

        expected_contents = self.fill_session_cart()
        response = self.client.get(url)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_shopping_cart_displays_total_cost(self):
        """
        Whole cart cost is correctly calculated and displayed.
        """
        url = self.user_access_url('orders:shopping_cart')

        expected_cart_cost = 0
        for item in self.fill_session_cart():
            expected_cart_cost += item['price'] * item['amount']

        self.client.get(url)
        self.assertEqual(self.client.session['cart_cost'], expected_cart_cost)


class UpdateCartViewTests(CustomTestCase):

    def test_update_shopping_cart(self):
        """
        Change amount of items from shopping cart page.
        """
        url = self.user_access_url('orders:shopping_cart')

        expected_contents = self.fill_session_cart()
        for item in expected_contents:
            update_url = reverse(ORDERS_UPDATE, args=(item['id'],))
            new_amount = randint(1, 10)
            self.client.post(update_url, {'amount': new_amount})
            item['amount'] = new_amount
            item['cost'] = new_amount * item['price']

        response = self.client.get(url)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_remove_item_from_cart(self):
        """
        Setting amount to 0 removes item from cart page.
        """
        url = self.user_access_url('orders:shopping_cart')

        expected_contents = self.fill_session_cart()
        index = randint(0, 2)
        update_url = reverse(
            ORDERS_UPDATE, args=(expected_contents[index]['id'],))
        new_amount = 0
        self.client.post(update_url, {'amount': new_amount})

        expected_contents.pop(index)

        response = self.client.get(url)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_update_order_menu_errors(self):
        """
        Error messages are sent from menu.views.update_cart,
        and returned page is orders.shopping_page.
        """
        self.login_test_user()
        item = self.fill_session_cart()[0]
        update_url = reverse(ORDERS_UPDATE, args=(item['id'],))
        new_amount = -1
        response = self.client.post(update_url, {'amount': new_amount},
                                    follow=True)

        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Incorrect amount." in message.message)
        self.assertFalse(self.client.session.modified)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, SHOP_CART_PAGE)


class RemoveItemViewTests(CustomTestCase):

    def test_remove_item(self):
        """
        View removes item from cart.
        """
        url = self.user_access_url('orders:shopping_cart')

        expected_contents = self.fill_session_cart()
        index = randint(0, 2)
        update_url = reverse(
            'orders:remove_item', args=(expected_contents[index]['id'],))
        self.client.post(update_url)

        expected_contents.pop(index)

        response = self.client.get(url)
        self.assertEqual(response.context['contents'], expected_contents)


class CheckoutViewTests(CustomTestCase):

    def test_can_not_access_checkout_with_empty_cart(self):
        """
        Trying to access checkout with an empty cart
        redirects to shopping cart page.
        """
        self.login_test_user()

        self.assert_redirect_and_error_msg(
            'orders:checkout', redirect_to='orders:shopping_cart',
            get=False, msg_text="Your cart is empty.")

    def test_can_access_checkout(self):
        """
        Users with non-empty cart can access checkout page.
        """
        self.login_test_user()
        self.fill_session_cart()
        url = reverse('orders:checkout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/checkout.html')


class ProcessOrderViewTests(CustomTestCase):

    def test_process_order_redirects_anon(self):
        """
        TEMPORARY - Process order redirects unauthorized users to login.
        """
        self.assert_redirect_and_error_msg(path='orders:process_order')

    def test_process_order_redirects_get(self):
        """
        Process order is only available with POST.
        """
        url = self.user_access_url('orders:process_order')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('orders:shopping_cart'))

    def test_process_empty_cart(self):
        """
        Trying to order an empty cart will redirect with error message.
        """
        self.login_test_user()

        self.assert_redirect_and_error_msg(
            'orders:process_order', redirect_to='orders:shopping_cart',
            get=False, msg_text="Your cart is empty.")

    def test_process_order(self):
        """
        Order is successfully transefrered from Session to database.
        """
        url = self.user_access_url('orders:process_order')

        expected_contents = self.fill_session_cart()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your order was placed.")
        # cart and cart_cost are flushed
        session = self.client.session
        self.assertEqual(session['cart'], {})
        self.assertEqual(session['cart_cost'], 0)

        placed_order = OrderInfo.objects.get(pk=1)
        order_contents = placed_order.ordercontents_set.all()
        # arbitrary 5 seconds to account for some fault
        self.assertTrue(
            timezone.now() - placed_order.ordered < timedelta(seconds=5))
        self.assertEqual(len(expected_contents), len(order_contents))
        for expected in expected_contents:
            # .get also raises exception if more or less than 1 match found
            db_contents = order_contents.get(menu_item__id=expected['id'])
            dict_from_db = {
                'id': db_contents.menu_item.id,
                'name': db_contents.menu_item.name,
                'price': db_contents.menu_item.price,
                'amount': db_contents.amount,
                'cost': db_contents.cost,
            }
            self.assertEqual(expected, dict_from_db)
