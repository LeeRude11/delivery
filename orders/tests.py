from django.test import TestCase
from django.contrib.auth.models import User

from .models import OrderInfo, OrderContents, OrderLog
from menu.models import MenuItem


def create_new_user():
    """Create a new user for tests"""
    user = User.objects.create_user('testuser', None, 'testpassword')
    return user


def create_menu_item():
    """Create a new MenuItem"""
    return MenuItem.objects.create(name='new dish', price=100)


def create_order_object():
    """With a user object and MenuItem objects create an order object"""
    return None


def create_new_order(user=None, order=None, menu_item=None, amount=1):
    user = user or create_new_user()
    order = order or OrderInfo.objects.create(user=user)
    menu_item = menu_item or create_menu_item()
    OrderContents.objects.create(
        order=order, menu_item=menu_item, amount=amount)


class OrderInfoTests(TestCase):

    def test_order_from_user(self):
        """Order is associated with user"""
        new_user = create_new_user()
        new_order = OrderInfo.objects.create(user=new_user)
        self.assertEqual(new_order.user, User.objects.get(id=1))
