from django.test import TestCase
from django.contrib.auth.models import User

from random import randint
from datetime import datetime

from .models import OrderInfo, OrderContents
from menu.models import MenuItem
# from .views import ShoppingCartView


def create_new_user():
    """Create a new user for tests"""
    return User.objects.create_user('testuser', None, 'testpassword')


def create_menu_item():
    """Create a new MenuItem"""
    return MenuItem.objects.create(name='new dish', price=100)


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


# class ShoppingCartViewTests(TestCase):
#     ShoppingCartView
#     pass
