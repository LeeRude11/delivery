from datetime import date
from django.db import transaction
from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()


class AccountsTestConstants(object):

    """
    Constants also exported to Selenium tests.
    """

    required_fields = [
        'phone_number',
        'first_name',
        'second_name',
        'street',
        'house',
        'password1',
        'password2',
    ]
    unrequired_fields = [
        'email',
        'date_of_birth',
        'apartment'
    ]
    guest_user_fields = [
        'phone_number',
        'first_name',
        'second_name',
        'street',
        'house',
        'apartment',
        'email',
    ]
    user_for_tests = {
        'phone_number': '12345',
        'password1': 'testpassword',
        'password2': 'testpassword',
        'first_name': 'test first name',
        'second_name': 'test second name',
        'email': 'test@example.com',
        'date_of_birth': date(1980, 1, 1),
        'street': 'test street',
        'house': 'test house',
        'apartment': 'test apartment'
    }
    login_fields = {
        # email is also suitable for username field
        'username': 'phone_number',
        'password': 'password1',
    }
    phone_format_variations = ['+12345', '1(23)45', '123-45']
    ARBITRARY_NEW_DATE = date(1990, 1, 1)

    def login_test_user(self):
        self.create_test_user()
        login_dict = {
            k: self.user_for_tests[v] for k, v in self.login_fields.items()}
        self.client.login(**login_dict)

    def user_without_password_fields(self):
        user = self.user_for_tests.copy()
        user.pop('password1')
        user.pop('password2')
        return user

    def user_for_create_user(self):
        user = self.user_without_password_fields()
        user['password'] = self.user_for_tests['password1']
        return user

    def guest_user_for_create_guest_user(self):
        return {k: self.user_for_tests[k] for k in self.guest_user_fields}

    def login_form_dict(self):
        """
        Return a dict to pass into login form.
        """
        form = {}
        for form_field, user_field in self.login_fields.items():
            form[form_field] = self.user_for_tests[user_field]
        return form

    def get_required_fields_user(self):
        return {
            field: self.user_for_tests[field] for field in self.required_fields
        }

    def get_profile_page_fields(self):
        """
        Profile page has all user info fields except password.
        """
        return self.user_without_password_fields().keys()

    def assert_single_user_fields(self, fields_dict):
        """
        Using provided fields dictionary,
        ensure its values are equal to corresponding user values.
        """
        user = USER_MODEL.objects.get()
        for field, value in fields_dict.items():
            user_value = getattr(user, field)
            self.assertEqual(user_value, value)

    NEW_PASSWORD = 'newtestpassword'

    def get_password_change_dict(self):
        return {
            'old_password': self.user_for_tests['password1'],
            'new_password1': self.NEW_PASSWORD,
            'new_password2': self.NEW_PASSWORD
        }

    def assert_db_integrity_error(self, user_dict):
        """
        Assert IntegrityError in an atomic transaction.
        """
        # with self.assertRaises(utils.IntegrityError):
        # TODO ValueError are raised in _create_user now
        with self.assertRaises(ValueError):
            with transaction.atomic():
                USER_MODEL.objects.create_user(**user_dict)

    def create_test_user(self):
        user_dict = self.user_for_create_user()
        return USER_MODEL.objects.create_user(
            **user_dict)

    def create_test_guest_user(self):
        guest_user_dict = self.guest_user_for_create_guest_user()
        return USER_MODEL.objects.create_guest_user(
            **guest_user_dict)


class LoginBrowserUserMixin(AccountsTestConstants):
    """
    A function used in selenium test suites.
    """

    def login_browser_user(self):
        """
        Create and login a test user.
        """
        # https://stackoverflow.com/a/22497239
        self.login_test_user()
        cookie = self.client.cookies['sessionid']
        self.browser.get(self.live_server_url + '/admin/')
        self.browser.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })