from django.test import TestCase
from django.urls import reverse

from random import randint

from django.contrib.auth.models import User
from .models import MenuItem


DEF_NAME = 'New Dish'
DEF_PRICE = 100


# Models tests
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


# Views tests
class MenuListViewTests(TestCase):

    def test_empty_menu_list(self):
        response = self.client.get(reverse('menu:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No items in menu")
        self.assertQuerysetEqual(response.context['object_list'], [])

    def test_menu_list_returned(self):
        new_menu_item = create_menu_item()
        response = self.client.get(reverse('menu:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['object_list'],
                                 ['<MenuItem: ' + new_menu_item.name + '>'])


class MenuItemAddToCartTests(TestCase):

    def test_non_user_can_not_order(self):
        """
        TEMPORARY - non authorized users can not add items to cart
        and redirected to login page.
        """
        new_menu_item = create_menu_item()
        url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
        response = self.client.post(url, {'amount': 1}, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Must be logged in." in message.message)

    def test_add_item_to_cart(self):
        """
        Adding an item on its View adds it to user's session object.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        new_menu_item = create_menu_item()
        amount = 1
        url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
        response = self.client.post(url, {'amount': amount})
        self.assertRedirects(response, reverse('menu:menu'))
        session = self.client.session
        expected_cart = {
            f'{new_menu_item.id}': f'{amount}'
        }
        self.assertEqual(session['cart'], expected_cart)

    def test_add_only_positive_ints_of_items(self):
        """
        Trigger an error message if provided item amount was 0, negative,
        float or string.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        new_menu_item = create_menu_item()
        amounts = [0, -1, 1.5, 'Hello']
        url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
        for amount in amounts:
            response = self.client.post(url, {'amount': amount}, follow=True)
            self.assertRedirects(response, reverse('menu:detail',
                                 args=(new_menu_item.id,)))
            message = list(response.context.get('messages'))[0]
            self.assertEqual(message.tags, 'error')
            self.assertTrue("Incorrect amount." in message.message)
        session = self.client.session
        self.assertRaises(KeyError, lambda: session['cart'])

    def test_error_when_amount_not_provided(self):
        """
        Trigger an error message if amount of the item wasn't provided.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        new_menu_item = create_menu_item()
        url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('menu:detail',
                             args=(new_menu_item.id,)))
        session = self.client.session
        message = list(response.context.get('messages'))[0]

        self.assertEqual(message.tags, 'error')
        self.assertTrue("Incorrect amount." in message.message)
        self.assertRaises(KeyError, lambda: session['cart'])

    def test_add_various_items_to_cart(self):
        """
        Different items are successfully added to cart.
        """
        User.objects.create_user('testuser', None, 'testpassword')
        self.client.login(username='testuser', password='testpassword')
        new_menu_items_list = [
            create_menu_item(name=f'Dish{i}') for i in range(3)]
        expected_cart = {}
        for new_menu_item in new_menu_items_list:
            url = reverse('menu:add_to_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            response = self.client.post(url, {'amount': amount})
            self.assertRedirects(response, reverse('menu:menu'))
            expected_cart[f'{new_menu_item.id}'] = f'{amount}'
        session = self.client.session
        self.assertEqual(session['cart'], expected_cart)
