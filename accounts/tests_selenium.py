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

    LOGIN_URL = reverse('accounts:login')
    LOGOUT_URL = reverse('accounts:logout')
    REGISTER_URL = reverse('accounts:register')
    PROFILE_URL = reverse('accounts:profile')
    PASS_CHANGE_URL = reverse('accounts:password_change')

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

    def fill_submit_form_with_values(self, form, values):
        """
        Fill a passed form with values from a dictionary,
        finding fields using its keys, and submit it.
        """
        for key, value in values.items():
            field = form.find_element_by_id('id_' + key)
            field.clear()
            # TODO can't pass datetime as is
            field.send_keys(str(value))
        form.submit()
        sleep(0.5)

    def assert_redirects_unauthorized(self, target_url):
        """
        Unauthorized users are redirected to login page
        with initial target url as next parameter.
        """
        # if user is logged in on setUp - log him out for this test
        logout_url = self.live_server_url + self.LOGOUT_URL
        self.browser.get(logout_url)

        url = self.live_server_url + target_url
        self.browser.get(url)

        redirected_url = (self.live_server_url + self.LOGIN_URL + '?next=' +
                          target_url)
        self.assertEqual(self.browser.current_url, redirected_url)


class RegisterTests(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        url = self.live_server_url + self.REGISTER_URL
        self.browser.get(url)

    def get_register_form(self):
        """
        Return register form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_register_fields(self):
        """
        All expected fields are rendered.
        """
        register_fields = self.user_for_tests.keys()
        self.verify_available_fields(register_fields)

    def test_register_empty(self):
        """
        Can not register with empty values in required fields.
        """
        ERROR_MSG = "This field is required."
        register_form = self.get_register_form()
        empty_required_fields = {
            field: "" for field in self.required_fields
        }
        self.fill_submit_form_with_values(register_form,
                                          empty_required_fields)
        # user was not created
        self.assertRaises(USER_MODEL.DoesNotExist, USER_MODEL.objects.get)
        # check that each field displays an error
        errorlist = self.browser.find_elements_by_class_name('errorlist')
        self.assertEqual(len(errorlist), len(self.required_fields))
        for error in errorlist:
            self.assertEqual(error.text, ERROR_MSG)

    def test_register_success(self):
        """
        Registration is successful and all provided fields are stored.
        """
        register_form = self.get_register_form()
        self.fill_submit_form_with_values(register_form,
                                          self.user_for_tests)
        user = USER_MODEL.objects.get()
        for field in self.user_without_password_fields():
            field_value = getattr(user, field)
            self.assertEqual(field_value, self.user_for_tests[field])
        self.assertTrue(user.check_password(self.user_for_tests['password1']))

    def test_register_unrequired(self):
        """
        Registration is successful without providing optional fields.
        """
        register_form = self.get_register_form()
        required_fields_user = self.get_required_fields_user()
        self.fill_submit_form_with_values(register_form,
                                          required_fields_user)
        user = USER_MODEL.objects.get()
        for field in self.unrequired_fields:
            field_value = getattr(user, field)
            self.assertTrue(field_value in (None, ''))


class LoginTests(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        url = self.live_server_url + self.LOGIN_URL
        self.browser.get(url)

    def get_login_form(self):
        """
        Return login form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_login_fields(self):
        """
        All expected fields are rendered.
        """
        self.verify_available_fields(self.login_fields.keys())

    def test_login_empty(self):
        """
        Can not login without providing credentials.
        """
        ERROR_MSG = ("Your username and password didn't match. " +
                     "Please try again.")
        self.create_new_user()

        self.assertTrue(self.browser.get_cookie('sessionid') is None)
        login_form = self.get_login_form()
        empty_login_fields = {
            field: "" for field in self.login_fields.keys()
        }
        self.fill_submit_form_with_values(login_form, empty_login_fields)
        error_element = self.browser.find_element_by_xpath(
            f'//p[text()="{ERROR_MSG}"]')
        self.assertTrue(error_element is not None)
        # user was not logged in
        self.assertTrue(self.browser.get_cookie('sessionid') is None)

    def test_login_success(self):
        """
        Provding correct values successfully logs the user in.
        """
        self.create_new_user()

        self.assertTrue(self.browser.get_cookie('sessionid') is None)

        login_form = self.get_login_form()
        self.fill_submit_form_with_values(login_form, self.login_form_dict())

        self.assertTrue(self.browser.get_cookie('sessionid') is not None)


class ProfileTests(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        self.login_browser_user()
        url = self.live_server_url + self.PROFILE_URL
        self.browser.get(url)

    def get_profile_update_form(self):
        """
        Return login form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_profile_redirects_unauthorized(self):
        """
        Profile page is only accessible by authorized users.
        """
        self.assert_redirects_unauthorized(self.PROFILE_URL)

    def test_profile_fields_rendered(self):
        """
        All expected fields are rendered.
        """
        self.verify_available_fields(self.get_profile_page_fields())

    def test_profile_fields_prefilled(self):
        """
        All expected fields are correctly pre-filled.
        """
        profile_fields = self.user_without_password_fields()
        for name, value in profile_fields.items():
            # django fields ids are formatted "id=id_{field_name}"
            field_id = 'id_' + name
            field = self.browser.find_element_by_id(field_id)
            self.assertEqual(
                field.get_attribute('value'), str(value)
            )

    def test_profile_page_change_password_link(self):
        """
        Profile page is rendered with a link to change password page.
        """
        PASS_CHANGE_TEXT = "Change Password"
        button = self.browser.find_element_by_link_text(PASS_CHANGE_TEXT)
        link = button.get_attribute('href')
        expected_link = self.live_server_url + self.PASS_CHANGE_URL
        self.assertEqual(link, expected_link)
        button.click()
        self.assertEqual(self.browser.current_url, expected_link)

    def test_profile_page_update_success(self):
        """
        By submitting a form on profile page,
        users are albe to update their info.
        """

        updated_user = {}
        for field in self.get_profile_page_fields():
            try:
                updated_user[field] = self.user_for_tests[field] + '1'
            except TypeError:
                # date field
                updated_user[field] = self.ARBITRARY_NEW_DATE

        update_form = self.get_profile_update_form()
        self.fill_submit_form_with_values(update_form, updated_user)
        user = USER_MODEL.objects.get()
        for field in self.user_without_password_fields():
            field_value = getattr(user, field)
            self.assertEqual(field_value, updated_user[field])


class PasswordChangeTests(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        self.login_browser_user()
        url = self.live_server_url + self.PASS_CHANGE_URL
        self.browser.get(url)

    def get_pass_change_form(self):
        """
        Return password change form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_pass_change_redirects_unauthorized(self):
        """
        Password change page is only accessible by authorized users.
        """
        self.assert_redirects_unauthorized(self.PASS_CHANGE_URL)

    def test_profile_fields_rendered(self):
        """
        All expected fields are rendered.
        """
        self.verify_available_fields(self.get_password_change_dict().keys())

    def test_change_password_success(self):
        """
        User's password is successfully updated.
        """

        user = USER_MODEL.objects.get()
        self.assertFalse(user.check_password(self.NEW_PASSWORD))

        new_password_form = self.get_password_change_dict()
        pass_change_form = self.get_pass_change_form()
        self.fill_submit_form_with_values(pass_change_form, new_password_form)

        user = USER_MODEL.objects.get()
        self.assertTrue(user.check_password(self.NEW_PASSWORD))

    def test_changed_password_logged_in(self):
        """
        Changing the password doesn't log the user out.
        """
        self.assertTrue(self.browser.get_cookie('sessionid') is not None)

        new_password_form = self.get_password_change_dict()
        pass_change_form = self.get_pass_change_form()
        self.fill_submit_form_with_values(pass_change_form, new_password_form)

        self.assertTrue(self.browser.get_cookie('sessionid') is not None)


class LogoutTests(FirefoxAccountsTests):

    def test_logout_authorized_user(self):
        """
        Logout view logs out authorized users.
        """

        self.login_browser_user()
        self.assertTrue(self.browser.get_cookie('sessionid') is not None)

        url = self.live_server_url + self.LOGOUT_URL
        self.browser.get(url)

        self.assertTrue(self.browser.get_cookie('sessionid') is None)

    def test_logout_anon_users_login(self):
        """
        Anonymous users accessing logout view are redirected to login page.
        """
        url = self.live_server_url + self.LOGOUT_URL
        self.browser.get(url)
        self.assertEqual(self.browser.current_url,
                         self.live_server_url + self.LOGIN_URL)
