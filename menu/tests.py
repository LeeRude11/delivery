from django.test import TestCase
from django.urls import reverse

from random import randint

from .models import MenuItem
from accounts.tests import AccountsTestConstants


class MenuTestConstants(object):

    DEF_DISH = {
        'name': 'New Dish',
        'price': 100
    }

    def change_item_amount_in_cart(self, item_id=None, amount=None,
                                   action='increase'):
        """
        Post an amount (provided OR random) of
        an item (provided OR the only available one).
        Return the randomized amount.
        """
        amount = amount or randint(1, 10)
        item_id = item_id or MenuItem.objects.get().id
        url = reverse('menu:update_cart')
        for i in range(amount):
            self.client.get(url, {'item_id': item_id, 'action': action})
        return amount

    def fill_session_cart(self):
        expected_contents = []
        for i in range(3):
            new_menu_item = MenuItem.objects.create(
                name=f'Dish{i}', price=randint(10, 300))
            amount = self.change_item_amount_in_cart(item_id=new_menu_item.id)
            expected_contents.append({
                'id': new_menu_item.id,
                'name': new_menu_item.name,
                'price': new_menu_item.price,
                'amount': amount,
                'cost': new_menu_item.price * amount
            })
        return expected_contents


class CustomTestCase(AccountsTestConstants, MenuTestConstants, TestCase):

    def add_menu_item(self):
        """
        Create a new menu item and return its id.
        """
        item_id = MenuItem.objects.create(**self.DEF_DISH).id
        return item_id

    def assert_session_key(self, key, expected):
        """
        A certain value is expected in session object.
        """
        session = self.client.session
        self.assertEqual(session[key], expected)


# Models tests
class MenuItemModelTests(CustomTestCase):

    def test_item_created(self):
        """
        a MenuItem can be created and retrieved.
        """
        new_menu_item = MenuItem.objects.create(**self.DEF_DISH)
        added_menu_item = MenuItem.objects.get()
        self.assertEqual(new_menu_item, added_menu_item)
        for field, value in self.DEF_DISH.items():
            db_value = getattr(added_menu_item, field)
            self.assertEqual(value, db_value)


# Views tests
class MenuListViewTests(CustomTestCase):

    def test_empty_menu_list(self):
        """
        App without menu items shows an empty menu.
        """
        response = self.client.get(reverse('menu:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No items in menu")
        self.assertQuerysetEqual(response.context['object_list'], [])

    def test_menu_list_returned(self):
        """
        A single item is shown.
        """
        new_menu_item = MenuItem.objects.create(**self.DEF_DISH)
        response = self.client.get(reverse('menu:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['object_list'],
                                 ['<MenuItem: ' + new_menu_item.name + '>'])


class MenuItemViewTests(CustomTestCase):

    def test_view_context_current_amount(self):
        """
        MenuItemView context has current amount of the item in cart.
        """
        item_id = self.add_menu_item()

        amount = self.change_item_amount_in_cart()
        url = reverse('menu:detail', args=(item_id,))
        response = self.client.get(url)
        self.assertEqual(response.context['current_amount'], amount)


class MenuItemUpdateCartTests(CustomTestCase):

    URL = reverse('menu:update_cart')

    def test_update_cart_post_only(self):
        """
        Only accept GET requests.
        """
        item_id = self.add_menu_item()
        response = self.client.post(
            self.URL, {'item_id': item_id, 'action': 'increase'}, follor=True)
        self.assertRedirects(response, reverse('menu:menu'))

    def test_get_without_action(self):
        """
        Request to update_cart without providing action query returns
        bad request.
        """
        item_id = self.add_menu_item()
        response = self.client.get(self.URL, {'item_id': item_id})
        self.assertEqual(response.status_code, 400)
        self.assert_session_key('cart', {})

    def test_wrong_action(self):
        """
        Passing improper action returns bad request
        """
        item_id = self.add_menu_item()
        response = self.client.get(
            self.URL, {'item_id': item_id, 'action': 'no_such_action'})
        self.assertEqual(response.status_code, 400)
        self.assert_session_key('cart', {})

    def test_decrease_below_zero(self):
        """
        Trying to decrease amount of item in cart below zero returns
        bad request.
        """
        item_id = self.add_menu_item()
        query = {'item_id': item_id, 'action': 'increase'}
        self.client.get(self.URL, query)

        query['action'] = 'decrease'

        self.client.get(self.URL, query)
        response = self.client.get(self.URL, query)

        self.assertEqual(response.status_code, 400)
        self.assert_session_key('cart', {})

    def test_success_json_cart_cost(self):
        """
        Successful update_cart request returns a JSON response
        with updated cart cost.
        """
        item_id = self.add_menu_item()
        query = {'item_id': item_id, 'action': 'increase'}
        response = self.client.get(self.URL, query)

        self.assertEqual(response.status_code, 200)
        expected_json = {
            'new_cost': self.DEF_DISH['price']
        }
        self.assertEqual(response.json(), expected_json)

        query['action'] = 'decrease'
        response = self.client.get(self.URL, query)
        expected_json['new_cost'] = 0
        self.assertEqual(response.json(), expected_json)

    def test_add_item_to_cart(self):
        """
        Adding an item on its View adds it to user's session object.
        """
        item_id = self.add_menu_item()

        item_added = self.change_item_amount_in_cart()
        amount = item_added

        expected_cart = {
            f'{item_id}': amount
        }
        self.assert_session_key('cart', expected_cart)

    def test_remove_some_items(self):
        """
        Cart is successfully updated after removing some items.
        """
        item_id = self.add_menu_item()

        added_amount = self.change_item_amount_in_cart(amount=randint(6, 10))
        removed_amount = self.change_item_amount_in_cart(
            amount=randint(1, 5), action='decrease')
        new_amount = added_amount - removed_amount

        expected_cart = {
            f'{item_id}': new_amount
        }
        self.assert_session_key('cart', expected_cart)

    def test_decrease_item_to_zero(self):
        """
        Item key is removed from cart if decreased to 0.
        """
        self.add_menu_item()

        amount = self.change_item_amount_in_cart()
        self.change_item_amount_in_cart(amount=amount, action='decrease')
        self.assert_session_key('cart', {})

    def test_remove_item_from_cart(self):
        """
        Remove action allows to remove the whole amount of item from cart.
        """
        self.add_menu_item()

        self.change_item_amount_in_cart()
        # removed should be accessed 1 time to remove whole item
        self.change_item_amount_in_cart(amount=1, action='remove')
        self.assert_session_key('cart', {})

    def test_add_various_items_to_cart(self):
        """
        Different items are successfully added to cart.
        """
        expected_cart = {}
        for item in self.fill_session_cart():
            expected_cart[f'{item["id"]}'] = item['amount']
        self.assert_session_key('cart', expected_cart)

    def test_cart_cost_added(self):
        """
        Cart cost is correctly calculated.
        """
        expected_cost = 0
        for item in self.fill_session_cart():
            expected_cost += item['price'] * item['amount']
        self.assert_session_key('cart_cost', expected_cost)

    def test_cart_cost_removes(self):
        """
        Cart cost is correcty updated after deleting item
        and after decreasing another item's amount.
        """
        contents = self.fill_session_cart()
        old_cost = self.client.session['cart_cost']

        item_to_remove = contents.pop(randint(0, len(contents) - 1))
        item_to_decrease = contents.pop(randint(0, len(contents) - 1))
        amount_to_decrease = randint(1, item_to_decrease['amount'])

        expected_loss = (item_to_remove['price'] * item_to_remove['amount'] +
                         item_to_decrease['price'] * amount_to_decrease)

        self.change_item_amount_in_cart(
            item_id=item_to_remove['id'], amount=item_to_remove['amount'],
            action='decrease')
        self.change_item_amount_in_cart(
            item_id=item_to_decrease['id'],
            amount=amount_to_decrease,
            action='decrease')

        self.assert_session_key('cart_cost', old_cost - expected_loss)


class MenuItemUpdateCartTestsLoggedIn(MenuItemUpdateCartTests):
    """
    Rerun those tests but with a logged in user.
    """

    def setUp(self):
        super().setUp()
        self.login_test_user()
