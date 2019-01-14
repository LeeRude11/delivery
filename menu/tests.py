from django.test import TestCase
from django.urls import reverse

from .models import MenuItem


DEF_NAME = 'New Dish'
DEF_PRICE = 100


class MenuItemModelTests(TestCase):

    def test_item_created(self):
        """
        a MenuItem can be created and retrieved.
        """
        dish = {
            'name': DEF_NAME,
            'price': DEF_PRICE
        }
        new_menu_item = MenuItem.objects.create(**dish)
        self.assertEqual(new_menu_item, MenuItem.objects.get(id=1))
        self.assertEqual(new_menu_item, MenuItem.objects.filter(
            price=dish['price']).get(name=dish['name']))


def create_menu_item(name=DEF_NAME, price=DEF_PRICE):
    """
    Create and return a menu item with given name and price.
    """
    new_menu_item = MenuItem.objects.create(name=name, price=price)
    return new_menu_item


class MenuListViewTests(TestCase):

    def test_empty_menu_list(self):
        response = self.client.get(reverse('menu:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No items in menu")
        self.assertQuerysetEqual(response.context['object_list'], [])

    def test_menu_list_returned(self):
        create_menu_item()
        response = self.client.get(reverse('menu:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['object_list'],
                                 ['<MenuItem: ' + DEF_NAME + '>'])
