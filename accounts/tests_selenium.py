from django.urls import reverse
from django.contrib.auth import get_user_model

from datetime import datetime, date

from core.tests_selenium import DeliveryFirefoxTests


USER_MODEL = get_user_model()


class FirefoxAccountsTests(DeliveryFirefoxTests):

    LOGIN_URL = reverse('accounts:login')
    LOGOUT_URL = reverse('accounts:logout')
    REGISTER_URL = reverse('accounts:register')
    PROFILE_URL = reverse('accounts:profile')
    PASS_CHANGE_URL = reverse('accounts:password_change')

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
        self.register_form = self.get_register_form()

    def get_register_form(self):
        """
        Return register form element.
        """
        return self.browser.find_element_by_tag_name('form')

    def test_register_fields(self):
        """
        All expected fields are rendered.
        """
        register_fields = self.user_form_user.keys()
        self.verify_available_fields(register_fields)

    def test_register_empty(self):
        """
        Can not register with empty values in required fields.
        """
        ERROR_MSG = "This field is required."
        empty_required_fields = {
            field: "" for field in self.required_fields
        }
        self.fill_submit_form_with_values(self.register_form,
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
        self.fill_submit_form_with_values(self.register_form,
                                          self.user_form_user)
        user = USER_MODEL.objects.get()
        for field in self.user_without_password_fields():
            field_value = getattr(user, field)
            self.assertEqual(field_value, self.user_for_tests[field])
        self.assertTrue(user.check_password(self.user_for_tests['password1']))

    def test_register_unrequired(self):
        """
        Registration is successful without providing optional fields.
        """
        required_fields_user = self.required_fields_user
        self.fill_submit_form_with_values(self.register_form,
                                          required_fields_user)
        user = USER_MODEL.objects.get()
        for field in self.unrequired_fields:
            field_value = getattr(user, field)
            self.assertTrue(field_value in (None, ''))

    def test_register_date_element(self):
        """
        Date of birth field is represented with three <select> elements.
        """
        for field in self.user_form_date_fields:
            id = f'id_{self.ORIG_DATE_FIELD}_{field}'
            found_field = self.register_form.find_element_by_id(id)
            self.assertEqual(found_field.tag_name, 'select')

    def test_register_years_hundred_and_up(self):
        """
        Years available for selection are descending from current to
        99 years ago.
        """
        CURRENT_YEAR = datetime.now().year
        YEARS_RANGE = 100

        year = self.register_form.find_element_by_id(
            f'id_{self.ORIG_DATE_FIELD}_year')
        options = year.find_elements_by_tag_name('option')

        # there's an empty option
        options.pop(0)
        self.assertEqual(len(options), YEARS_RANGE)
        descending = range(CURRENT_YEAR, CURRENT_YEAR - YEARS_RANGE, -1)
        for option, year in zip(options, descending):
            self.assertEqual(int(option.text), year)


class LoginTests(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        url = self.live_server_url + self.LOGIN_URL
        self.browser.get(url)
        self.login_form = self.get_login_form()

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
        self.create_test_user()

        self.assertTrue(self.browser.get_cookie('sessionid') is None)
        empty_login_fields = {
            field: "" for field in self.login_fields.keys()
        }
        self.fill_submit_form_with_values(self.login_form, empty_login_fields)
        error_element = self.browser.find_element_by_xpath(
            f'//p[text()="{ERROR_MSG}"]')
        self.assertTrue(error_element is not None)
        # user was not logged in
        self.assertTrue(self.browser.get_cookie('sessionid') is None)

    def test_login_success(self):
        """
        Provding correct values successfully logs the user in.
        """
        self.create_test_user()

        self.assertTrue(self.browser.get_cookie('sessionid') is None)

        self.fill_submit_form_with_values(
            self.login_form, self.login_form_dict)

        self.assertTrue(self.browser.get_cookie('sessionid') is not None)

    def test_login_register_link(self):
        """
        Login page has a link to register page.
        """
        LOGIN_ALT = self.browser.find_element_by_id('login-alt')
        link = self.link_exists(LOGIN_ALT, self.REGISTER_URL)
        self.assertEqual(link.text, 'Registration')

    def not_test_login_forgot_pass(self):
        """
        Login page has a link to password restore.
        """
        # TODO


class ProfileTests(FirefoxAccountsTests):

    def setUp(self):
        super().setUp()
        self.login_browser_user()
        url = self.live_server_url + self.PROFILE_URL
        self.browser.get(url)
        self.update_form = self.get_profile_update_form()

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
        self.verify_available_fields(self.user_form_profile_user.keys())

    def test_profile_fields_prefilled(self):
        """
        All expected fields are correctly pre-filled.
        """
        profile_fields = self.user_form_profile_user
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
        full_date = {}
        for field, value in self.user_form_profile_user.items():
            try:
                updated_user[field] = value + '1'
            except TypeError:
                # int of date field
                updated_user[field] = str(value + 1)

                short_field = field.split(f'{self.ORIG_DATE_FIELD}_')[1]
                full_date[short_field] = value + 1

        self.fill_submit_form_with_values(self.update_form, updated_user)

        user = USER_MODEL.objects.get()
        updated_user[self.ORIG_DATE_FIELD] = date(**full_date)

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
        self.verify_available_fields(self.password_change_dict.keys())

    def test_change_password_success(self):
        """
        User's password is successfully updated.
        """

        user = USER_MODEL.objects.get()
        self.assertFalse(user.check_password(self.NEW_PASSWORD))

        new_password_form = self.password_change_dict
        pass_change_form = self.get_pass_change_form()
        self.fill_submit_form_with_values(pass_change_form, new_password_form)

        user = USER_MODEL.objects.get()
        self.assertTrue(user.check_password(self.NEW_PASSWORD))

    def test_changed_password_logged_in(self):
        """
        Changing the password doesn't log the user out.
        """
        self.assertTrue(self.browser.get_cookie('sessionid') is not None)

        new_password_form = self.password_change_dict
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
