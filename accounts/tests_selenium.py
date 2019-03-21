# from menu.tests_selenium import FirefoxTests
# TODO common operations? reusable apps?
from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from .tests import AccountsTestConstants
from time import sleep

USER_MODEL = get_user_model()


class FirefoxAccountsTests(StaticLiveServerTestCase, AccountsTestConstants):

    def create_new_user(self):
        """Create a new user for tests"""
        return USER_MODEL.objects.create_user(
            **self.user_for_create_user()
        )

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.close()

    def login_browser_user(self):
        """
        Create and login a test user.
        """
        # https://stackoverflow.com/a/22497239
        user = self.create_new_user()
        self.client.login(username=user.phone_number, password='testpassword')
        cookie = self.client.cookies['sessionid']
        self.browser.get(self.live_server_url + '/admin/')
        self.browser.add_cookie({
            'name': 'sessionid',
            'value': cookie.value,
            'secure': False,
            'path': '/'
        })

    def verify_available_fields(self, ids_list):
        """
        With a list of passed elements,
        verify that corresponding input elements are present on the page.
        """
        for field_name in ids_list:
            # django fields ids are formatted "id=id_{field_name}"
            field_id = 'id_' + field_name
            self.assertEqual(
                len(self.browser.find_elements_by_id(field_id)), 1
            )


class RegisterTests(FirefoxAccountsTests):

    def get_register_form(self):
        """
        Return register form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_register_fields(self):
        """
        All expected fields are rendered.
        """
        url = self.live_server_url + reverse('accounts:register')
        self.browser.get(url)
        register_fields = self.user_for_tests.keys()
        self.verify_available_fields(register_fields)

    def test_register_empty(self):
        """
        Can't POST with empty required fields.
        """
        ERROR_MSG = "This field is required."
        url = self.live_server_url + reverse('accounts:register')
        self.browser.get(url)
        register_form = self.get_register_form()
        for req_field in self.required_fields:
            field = register_form.find_element_by_id('id_' + req_field)
            field.clear()
            field.send_keys()
        register_form.submit()
        # user was not created
        self.assertRaises(USER_MODEL.DoesNotExist, USER_MODEL.objects.get)
        # check that each field displays an error
        sleep(0.5)
        errorlist = self.browser.find_elements_by_class_name('errorlist')
        self.assertEqual(len(errorlist), len(self.required_fields))
        for error in errorlist:
            self.assertEqual(error.text, ERROR_MSG)

    def test_register_success(self):
        """
        Registration is successful and all provided fields are stored.
        """
        url = self.live_server_url + reverse('accounts:register')
        self.browser.get(url)
        register_form = self.get_register_form()
        for key, value in self.user_for_tests.items():
            field = register_form.find_element_by_id('id_' + key)
            field.clear()
            # TODO can't pass datetime as is
            field.send_keys(str(value))
        register_form.submit()
        sleep(0.5)
        user = USER_MODEL.objects.get()
        for field in self.user_without_password_fields():
            field_value = getattr(user, field)
            self.assertEqual(field_value, self.user_for_tests[field])
        self.assertTrue(user.check_password(self.user_for_tests['password1']))

    def test_register_unrequired(self):
        """
        Registration is successful without providing optional fields.
        """
        url = self.live_server_url + reverse('accounts:register')
        self.browser.get(url)
        register_form = self.get_register_form()
        for key in self.required_fields:
            field = register_form.find_element_by_id('id_' + key)
            field.clear()
            field.send_keys(self.user_for_tests[key])
        register_form.submit()
        sleep(0.5)
        user = USER_MODEL.objects.get()
        for field in self.unrequired_fields:
            field_value = getattr(user, field)
            self.assertTrue(field_value in (None, ''))

    def test_(self):
        """
        """
        # TODO


class LoginTests(FirefoxAccountsTests):

    pass
    # TODO


class ProfileTests(FirefoxAccountsTests):

    def test_profile_page_change_password_link(self):
        """
        Profile page is rendered with a link to change password page.
        """
        # TODO
    # TODO
