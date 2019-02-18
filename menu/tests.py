from django.test import TestCase
from django.urls import reverse

from random import randint

from .models import MenuItem
from orders.tests import CustomTestCase


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


class MenuCustomTestCase(CustomTestCase):

    def login_user_add_item_return_url_and_id(self):
        """
        Login user, create a new menu item and return a tuple(
        url with its id in args, id itself)
        """
        self.login_test_user()
        new_menu_item = create_menu_item()
        item_id = new_menu_item.id
        return (reverse('menu:update_cart', args=(item_id,)), item_id)

    def post_to_cart_redirect_return_response(self, url, amount=None):
        """
        Make POST request to cart, assertRedirect and return Response.
        """
        amount = amount or randint(1, 10)
        response = self.client.post(url, {'amount': amount}, folow=True)
        self.assertRedirects(response, reverse('menu:menu'))
        return response


class MenuItemViewTests(MenuCustomTestCase):

    def test_view_context_current_amount(self):
        """
        MenuItemView context has current amount of the item in cart.
        """
        add_url, menu_item_id = self.login_user_add_item_return_url_and_id()
        amount = randint(1, 10)
        self.client.post(add_url, {'amount': amount})
        url = reverse('menu:detail', args=(menu_item_id,))
        response = self.client.get(url)
        self.assertEqual(response.context['current_amount'], amount)


class MenuItemUpdateCartTests(MenuCustomTestCase):

    def test_non_user_can_not_order(self):
        """
        TEMPORARY - non authorized users can not add items to cart
        and redirected to login page.
        """
        new_menu_item = create_menu_item()
        url = reverse('menu:update_cart', args=(new_menu_item.id,))

        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
        message = list(response.context.get('messages'))[0]
        self.assertEqual(message.tags, 'error')
        self.assertTrue("Must be logged in." in message.message)

    def test_update_cart_post_only(self):
        """
        Only accept POST requests.
        """
        url, menu_item_id = self.login_user_add_item_return_url_and_id()
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('menu:detail',
                             args=(menu_item_id,)))

    def test_add_item_to_cart(self):
        """
        Adding an item on its View adds it to user's session object.
        """
        url, menu_item_id = self.login_user_add_item_return_url_and_id()

        amount = randint(1, 10)
        self.post_to_cart_redirect_return_response(url, amount)
        session = self.client.session
        expected_cart = {
            f'{menu_item_id}': f'{amount}'
        }
        self.assertEqual(session['cart'], expected_cart)

    def test_deny_non_ints_and_negative(self):
        """
        Trigger an error message if provided item amount was negative,
        or wasn't an integer.
        """
        url, menu_item_id = self.login_user_add_item_return_url_and_id()

        amounts = [-1, 1.5, 'Hello']
        for amount in amounts:
            response = self.client.post(url, {'amount': amount}, follow=True)
            self.assertRedirects(response, reverse('menu:detail',
                                 args=(menu_item_id,)))
            message = list(response.context.get('messages'))[0]
            self.assertEqual(message.tags, 'error')
            self.assertTrue("Incorrect amount." in message.message)
        session = self.client.session
        self.assertRaises(KeyError, lambda: session['cart'])

    def test_remove_some_items(self):
        """
        Cart is successfully updated after removing some items.
        """
        url, menu_item_id = self.login_user_add_item_return_url_and_id()

        amount = randint(6, 10)
        self.client.post(url, {'amount': amount})
        new_amount = randint(1, 5)
        self.client.post(url, {'amount': new_amount})
        session = self.client.session
        expected_cart = {
            f'{menu_item_id}': f'{new_amount}'
        }
        self.assertEqual(session['cart'], expected_cart)

    def test_remove_all_items(self):
        """
        Item key is removed from cart if provided amount is 0.
        """
        url, menu_item_id = self.login_user_add_item_return_url_and_id()

        amount = randint(1, 10)
        self.client.post(url, {'amount': amount})
        self.client.post(url, {'amount': 0})
        session = self.client.session
        expected_cart = {}
        self.assertEqual(session['cart'], expected_cart)

    def test_error_when_amount_not_provided(self):
        """
        Trigger an error message if amount of the item wasn't provided.
        """
        url, menu_item_id = self.login_user_add_item_return_url_and_id()

        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('menu:detail',
                             args=(menu_item_id,)))
        session = self.client.session
        message = list(response.context.get('messages'))[0]

        self.assertEqual(message.tags, 'error')
        self.assertTrue("Incorrect amount." in message.message)
        self.assertRaises(KeyError, lambda: session['cart'])

    def test_add_various_items_to_cart(self):
        """
        Different items are successfully added to cart.
        """
        self.login_test_user()
        expected_cart = {}
        for i in range(3):
            new_menu_item = create_menu_item(name=f'Dish{i}')
            url = reverse('menu:update_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            self.client.post(url, {'amount': amount})
            expected_cart[f'{new_menu_item.id}'] = f'{amount}'
        session = self.client.session
        self.assertEqual(session['cart'], expected_cart)

    def test_cart_cost_correct(self):
        """
        Cart cost is correctly calculated.
        """
        self.login_test_user()
        expected_cost = 0
        for i in range(3):
            new_menu_item = create_menu_item(name=f'Dish{i}')
            url = reverse('menu:update_cart', args=(new_menu_item.id,))
            amount = randint(1, 10)
            self.client.post(url, {'amount': amount})
            expected_cost += amount * new_menu_item.price
        session = self.client.session
        self.assertEqual(session['cart_cost'], expected_cost)
