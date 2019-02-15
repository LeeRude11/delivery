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


class ShoppingCartViewTests(TestCase):

    def test_shoping_cart_redirects_anon_to_login(self):
        """
        TEMPORARY - unauthorized users can not access shopping cart page.
        """
        url = reverse('orders:shopping_cart')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Must be logged in." in message.message)

    def test_shoping_cart_is_empty(self):
        """
        Opening page with empty cart displays appropriate text.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        url = reverse('orders:shopping_cart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your shopping cart is empty.")
        self.assertQuerysetEqual(response.context['contents'], [])

    def test_shoping_cart_not_empty(self):
        """
        Page has user's cart contents.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        url = reverse('orders:shopping_cart')

        new_menu_items_list = [
            create_menu_item(name=f'Dish{i}') for i in range(3)]
        expected_contents = []
        for new_menu_item in new_menu_items_list:
            add_url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            self.client.post(add_url, {'amount': amount})
            expected_contents.append({
                'name': new_menu_item.name,
                'price': new_menu_item.price,
                'amount': amount,
                'cost': new_menu_item.price * amount
            })

        response = self.client.get(url)
        self.assertEqual(response.context['contents'], expected_contents)

    def test_shoping_cart_displays_total_cost(self):
        """
        Whole cart cost is correctly calculated and displayed.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        url = reverse('orders:shopping_cart')

        new_menu_items_list = [
            create_menu_item(
                name=f'Dish{i}', price=randint(10, 300)) for i in range(3)]
        expected_cart_cost = 0
        for new_menu_item in new_menu_items_list:
            add_url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            expected_cart_cost += amount * new_menu_item.price
            self.client.post(add_url, {'amount': amount})

        response = self.client.get(url)
        self.assertEqual(response.context['cart_cost'], expected_cart_cost)

    def test_process_order_redirects_anon(self):
        """
        TEMPORARY - Process order redirects unauthorized users to login.
        """
        url = reverse('orders:process_order')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Must be logged in." in message.message)

    def test_process_order_redirects_get(self):
        """
        Process order is only available with POST.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        url = reverse('orders:process_order')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('orders:shopping_cart'))

    def test_process_empty_cart(self):
        """
        Trying to order an empty cart will redirect with error message.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        url = reverse('orders:process_order')
        response = self.client.post(url, follow=True)

        self.assertRedirects(response, reverse('orders:shopping_cart'))
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Your cart is empty." in message.message)

    def test_process_order(self):
        """
        Order is successfully transefrered from Session to database.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')

        new_menu_items_list = [
            create_menu_item(name=f'Dish{i}') for i in range(3)]
        expected_contents = []
        for new_menu_item in new_menu_items_list:
            add_url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            self.client.post(add_url, {'amount': amount})
            expected_contents.append({
                'name': new_menu_item.name,
                'price': new_menu_item.price,
                'amount': amount,
                'cost': new_menu_item.price * amount
            })

        url = reverse('orders:process_order')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your order was placed.")

        placed_order = OrderInfo.objects.get(pk=1)
        order_contents = placed_order.ordercontents_set.all()
        # arbitrary 5 seconds to account for some fault
        self.assertTrue(
            timezone.now() - placed_order.ordered < timedelta(seconds=5))
        self.assertEqual(len(expected_contents), len(order_contents))
        for expected in expected_contents:
            db_contents = order_contents.get(menu_item__name=expected['name'])
            dict_from_db = {
                'name': db_contents.menu_item.name,
                'price': db_contents.menu_item.price,
                'amount': db_contents.amount,
                'cost': db_contents.cost,
            }
            self.assertEqual(expected, dict_from_db)
