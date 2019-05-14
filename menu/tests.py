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

    def fill_session_cart(self):
        expected_contents = []
        for i in range(3):
            new_menu_item = MenuItem.objects.create(
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


class CustomTestCase(AccountsTestConstants, MenuTestConstants, TestCase):

    def add_menu_item(self):
        """
        Create a new menu item and return its id.
        """
        item_id = MenuItem.objects.create(**self.DEF_DISH).id
        return item_id

    def add_item_to_cart(self, item_id=None, amount=None):
        """
        Post [provided | random] amount of
        [provided | the only available one] item.
        Return response object and randomized amount.
        """
        if amount is None:
            amount = randint(1, 10)
        if item_id is None:
            # TODO the only one or should make it the last one?
            item_id = MenuItem.objects.get().id
        url = reverse('menu:update_cart', args=(item_id,))
        response = self.client.post(url, {'amount': amount}, follow=True)
        return {
            'response': response,
            'amount': amount
            }


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

        amount = self.add_item_to_cart()['amount']
        url = reverse('menu:detail', args=(item_id,))
        response = self.client.get(url)
        self.assertEqual(response.context['current_amount'], amount)


class MenuItemUpdateCartTests(CustomTestCase):

    def test_update_cart_post_only(self):
        """
        Only accept POST requests.
        """
        item_id = self.add_menu_item()
        url = reverse('menu:update_cart', args=(item_id,))
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('menu:detail',
                             args=(item_id,)))

    def test_add_item_to_cart(self):
        """
        Adding an item on its View adds it to user's session object.
        """
        item_id = self.add_menu_item()

        item_added = self.add_item_to_cart()
        response, amount = item_added['response'], item_added['amount']
        self.assertRedirects(response, reverse('menu:menu'))

        session = self.client.session
        expected_cart = {
            f'{item_id}': f'{amount}'
        }
        self.assertEqual(session['cart'], expected_cart)

    def test_deny_non_ints_and_negative(self):
        """
        Trigger an error message if provided item amount was negative,
        or wasn't an integer.
        """
        item_id = self.add_menu_item()

        amounts = [-1, 1.5, 'Hello']
        for amount in amounts:
            response = self.add_item_to_cart(amount=amount)['response']
            self.assertRedirects(response, reverse('menu:detail',
                                 args=(item_id,)))
            message = list(response.context.get('messages'))[0]
            self.assertEqual(message.tags, 'error')
            self.assertTrue("Incorrect amount." in message.message)
        session = self.client.session
        self.assertRaises(KeyError, lambda: session['cart'])

    def test_remove_some_items(self):
        """
        Cart is successfully updated after removing some items.
        """
        item_id = self.add_menu_item()

        self.add_item_to_cart(amount=randint(6, 10))
        new_amount = self.add_item_to_cart(amount=randint(1, 5))['amount']

        session = self.client.session
        expected_cart = {
            f'{item_id}': f'{new_amount}'
        }
        self.assertEqual(session['cart'], expected_cart)

    def test_remove_all_items(self):
        """
        Item key is removed from cart if provided amount is 0.
        """
        self.add_menu_item()

        self.add_item_to_cart()
        self.add_item_to_cart(amount=0)
        session = self.client.session
        expected_cart = {}
        self.assertEqual(session['cart'], expected_cart)

    def test_error_when_amount_not_provided(self):
        """
        Trigger an error message if amount of the item wasn't provided.
        """
        item_id = self.add_menu_item()
        url = reverse('menu:update_cart', args=(item_id,))

        response = self.client.post(url, follow=True)
        self.assertRedirects(response, reverse('menu:detail',
                             args=(item_id,)))
        session = self.client.session
        message = list(response.context.get('messages'))[0]

        self.assertEqual(message.tags, 'error')
        self.assertTrue("Incorrect amount." in message.message)
        self.assertRaises(KeyError, lambda: session['cart'])

    def test_add_various_items_to_cart(self):
        """
        Different items are successfully added to cart.
        """
        expected_cart = {}
        for item in self.fill_session_cart():
            expected_cart[str(item['id'])] = str(item['amount'])
        session = self.client.session
        self.assertEqual(session['cart'], expected_cart)

    def test_cart_cost_added(self):
        """
        Cart cost is correctly calculated.
        """
        expected_cost = 0
        for item in self.fill_session_cart():
            expected_cost += item['price'] * item['amount']
        session = self.client.session
        self.assertEqual(session['cart_cost'], expected_cost)

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

        self.add_item_to_cart(item_id=item_to_remove['id'], amount=0)
        self.add_item_to_cart(
            item_id=item_to_decrease['id'],
            amount=(item_to_decrease['amount'] - amount_to_decrease))

        new_cost = self.client.session['cart_cost']
        self.assertEqual(old_cost - expected_loss, new_cost)


class MenuItemUpdateCartTestsLoggedIn(MenuItemUpdateCartTests):
    """
    Rerun those tests but with a logged in user.
    """

    def setUp(self):
        super().setUp()
        self.login_test_user()
