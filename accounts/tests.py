from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from django.contrib import auth

EMAIL = 'test@example.com'
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
    user_for_tests = {
        'phone_number': '12345',
        'password1': 'testpassword',
        'password2': 'testpassword',
        'first_name': 'test first name',
        'second_name': 'test second name',
        'email': EMAIL,
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

    def user_without_password_fields(self):
        user = self.user_for_tests.copy()
        user.pop('password1')
        user.pop('password2')
        return user

    def user_for_create_user(self):
        user = self.user_without_password_fields()
        user['password'] = self.user_for_tests['password1']
        return user

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


class UserModelTests(TestCase, AccountsTestConstants):

    def test_user_created(self):
        """
        User is created using create_user()
        """
        new_user = USER_MODEL.objects.create_user(
            **self.user_for_create_user())
        self.assertEqual(new_user, USER_MODEL.objects.get())

    def test_superuser_created(self):
        """
        Superuser is created using create_superuser()
        """
        new_superuser = USER_MODEL.objects.create_superuser(
            *("1" for i in range(6)))
        self.assertEqual(new_superuser, USER_MODEL.objects.get())
        self.assertTrue(USER_MODEL.objects.get().is_admin)


class AccountsTestCase(TestCase, AccountsTestConstants):

    """
    Methods for tests.
    """

    def register_user(self):
        """
        POST a register form.
        """
        user = self.user_for_tests.copy()
        url = reverse('accounts:register')
        self.client.post(url, user, follow=True)

    def no_error_msgs(self, response):
        """
        Response doesn't have error messages.
        """
        self.assertEqual(response.context['form'].errors, {})


class RegisterViewTests(AccountsTestCase):

    def test_register_success(self):
        """
        Registration is successful and user object is saved.
        """
        url = reverse('accounts:register')
        form_to_post = self.user_for_tests.copy()
        self.assertEqual(len(USER_MODEL.objects.all()), 0)
        self.client.post(url, form_to_post, follow=True)
        user = USER_MODEL.objects.get()
        self.assert_single_user_fields(self.user_without_password_fields())
        self.assertTrue(user.check_password(form_to_post['password1']))

    def test_register_empty(self):
        """
        Can not register with empty values in required fields.
        """
        url = reverse('accounts:register')
        form_to_post = {}
        self.assertEqual(len(USER_MODEL.objects.all()), 0)
        for i, field in enumerate(self.required_fields):
            form_to_post[field] = self.user_for_tests[field]
            response = self.client.post(url, form_to_post, follow=True)
            try:
                self.assertFalse(field in response.context['form'].errors)
                next_field = self.required_fields[i+1]
            except (IndexError, KeyError):
                # TODO KeyError as no form in /profile redirected to
                # all required fields are filled and user is registered
                self.assertEqual(len(USER_MODEL.objects.all()), 1)
            else:
                self.assertContains(response, "This field is required")
                self.assertTrue(next_field in response.context['form'].errors)

    def test_register_unrequired(self):
        """
        Unrequired fields are...unrequired.
        """
        # CharField can't be stored as NULL(None)
        APARTMENT_VALUE = ''

        url = reverse('accounts:register')
        user = self.get_required_fields_user()
        self.client.post(url, user, follow=True)

        unrequired_dict = {key: None for key in self.unrequired_fields}
        unrequired_dict['apartment'] = APARTMENT_VALUE
        self.assert_single_user_fields(unrequired_dict)

    def test_register_unrequired_stored(self):
        """
        Unrequired fields are stored if provided.
        """
        url = reverse('accounts:register')
        self.client.post(url, self.user_for_tests, follow=True)

        unrequired_dict = {
            key: self.user_for_tests[key] for key in self.unrequired_fields}
        self.assert_single_user_fields(unrequired_dict)

    def test_register_standard_phone(self):
        """
        Provided phone number is standardized before saving.
        """
        user = self.user_for_tests.copy()
        url = reverse('accounts:register')
        for variation in self.phone_format_variations:
            user['phone_number'] = variation
            self.client.post(url, user, follow=True)
            added_user = USER_MODEL.objects.get()
            self.assertEqual(
                added_user.phone_number, self.user_for_tests['phone_number'])
            added_user.delete()

    def test_phone_no_digits(self):
        """
        Phone number with no digits returns error.
        """
        user = self.user_for_tests.copy()
        url = reverse('accounts:register')
        user['phone_number'] = '+abc!'
        response = self.client.post(url, user, follow=True)
        self.assertTrue('phone_number' in response.context['form'].errors)
        self.assertEqual(len(USER_MODEL.objects.all()), 0)

    def test_phone_email_unique(self):
        """
        Can't register users with same phone number or email.
        """
        first_user = self.user_for_tests.copy()
        url = reverse('accounts:register')
        self.client.post(url, first_user, follow=True)

        second_user = self.user_for_tests.copy()
        response = self.client.post(url, second_user, follow=True)
        self.assertTrue('phone_number' in response.context['form'].errors)
        self.assertTrue('email' in response.context['form'].errors)

        second_user['email'] = f"another{EMAIL}"
        response = self.client.post(url, second_user, follow=True)
        self.assertTrue('phone_number' in response.context['form'].errors)
        self.assertFalse('email' in response.context['form'].errors)

        second_user['phone_number'] = f'0{first_user["phone_number"]}'
        response = self.client.post(url, second_user, follow=True)
        self.no_error_msgs(response)

        self.assertEqual(len(USER_MODEL.objects.all()), 2)

    def test_register_success_logs_in(self):
        """
        Successful registration automatically logs the new user in.
        """
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        self.register_user()
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_register_date_format(self):
        """
        Date format?
        """
        # TODO


class LoginViewTests(AccountsTestCase):

    def test_login_empty(self):
        """
        Trying to log in with empty fields
        refreshes the page with an error message.
        """
        self.register_user()
        url = reverse('accounts:login')

        form_to_post = {}
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('username' in response.context['form'].errors)
        self.assertTrue('password' in response.context['form'].errors)

        form_to_post['username'] = self.user_for_tests['phone_number']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertFalse('username' in response.context['form'].errors)
        self.assertTrue('password' in response.context['form'].errors)

        form_to_post['password'] = self.user_for_tests['password1']
        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)
        self.assertRedirects(response, reverse('accounts:profile'))

    def test_login_incorrect(self):
        """
        Trying to log in with incorrect credentials
        refreshes the page with an error message.
        """
        self.register_user()
        url = reverse('accounts:login')

        form_to_post = {
            'username': self.user_for_tests['phone_number'] + '1',
            'password': self.user_for_tests['password1'] + '1',
        }
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('__all__' in response.context['form'].errors)

        form_to_post['username'] = self.user_for_tests['phone_number']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('__all__' in response.context['form'].errors)

        form_to_post['password'] = self.user_for_tests['password1']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertRedirects(response, reverse('accounts:profile'))
        self.no_error_msgs(response)

    def test_login_with_various_phone_formats(self):
        """
        Provided phone number is formatted to pass if correct.
        """
        self.register_user()
        url = reverse('accounts:login')
        form_to_post = {
            'password': self.user_for_tests['password1']
        }
        for variation in self.phone_format_variations:
            form_to_post['username'] = variation
            response = self.client.post(url, form_to_post, follow=True)
            self.no_error_msgs(response)
            self.assertRedirects(response, reverse('accounts:profile'))

    def test_login_with_email(self):
        """
        If user provided an email on registration,
        check his input against it and log in on success.
        """
        self.register_user()
        url = reverse('accounts:login')
        form_to_post = {
            'username': self.user_for_tests['email'],
            'password': self.user_for_tests['password1']
        }
        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)

    def test_email_case_indifferent(self):
        """
        Email is stored in lowercase and email provided to login
        converted to lowercase before verifying.
        """
        self.register_user()
        url = reverse('accounts:login')
        form_to_post = {
            'username': self.user_for_tests['email'].upper(),
            'password': self.user_for_tests['password1']
        }
        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)

    def test_login_next_redirect(self):
        """
        Redirected to login and logged in users
        proceed according to next parameter.
        """
        # TODO move this test to delivery app selenium tests
        # OR accounts selenium?..

    def test_login_username_errors(self):
        """
        Login page error tells user to provide either email or phone number.
        """
        error_message = " ".join(["Please enter a correct phone number",
                                 "(or email) and password."])

        url = reverse('accounts:login')
        form_to_post = {
            'username': self.user_for_tests['email'] + '1',
            'password': self.user_for_tests['password1'] + '1'
        }
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue(
            error_message in dict(response.context['form'].errors)['__all__'])


class ProfileViewTests(AccountsTestCase):

    """
    Profile view uses a reduced version of the same form as Register view,
    making form validation tests unnecessary.
    """

    def test_profile_login_required(self):
        """
        Only authorized users can access profile page.
        """
        profile_url = reverse('accounts:profile')
        error_msg = "Please login to see this page."
        next_url = reverse('accounts:login') + '?next=' + profile_url

        response = self.client.get(profile_url, follow=True)
        self.assertRedirects(response, next_url)
        self.assertContains(response, error_msg)

        self.register_user()
        response = self.client.get(profile_url, follow=True)
        self.assertNotContains(response, error_msg)

    def test_profile_displays_form(self):
        """
        Profile page displays a form similar to registration form
        but without passwords fields.
        """
        self.register_user()
        url = reverse('accounts:profile')
        response = self.client.get(url, follow=True)
        form_fields = list(response.context['form'].fields.keys())

        profile_page_fields = self.get_profile_page_fields()
        self.assertEqual(len(form_fields), len(profile_page_fields))
        for field in profile_page_fields:
            try:
                form_fields.remove(field)
            except ValueError:
                # profile field was not found in fields rendered for the page
                raise AssertionError
        self.assertEqual(len(form_fields), 0)

    def test_profile_form_prefilled(self):
        """
        Profile page form is prefilled with user info.
        """
        self.register_user()
        url = reverse('accounts:profile')
        response = self.client.get(url, follow=True)
        form_fields_w_values = response.context['form'].initial
        for k, v in form_fields_w_values.items():
            self.assertEqual(v, self.user_for_tests[k])

    def test_profile_page_update_success(self):
        """
        Users are able to update their information.
        """
        self.register_user()
        url = reverse('accounts:profile')

        updated_user = {}
        for field in self.get_profile_page_fields():
            try:
                updated_user[field] = self.user_for_tests[field] + '1'
            except TypeError:
                # date field
                updated_user[field] = self.ARBITRARY_NEW_DATE
        self.client.post(url, updated_user, follow=True)
        response = self.client.get(url, follow=True)
        form_fields_w_values = response.context['form'].initial
        for k, v in form_fields_w_values.items():
            self.assertEqual(v, updated_user[k])


class PasswordChangeViewTests(AccountsTestCase):

    def test_password_change_login_required(self):
        """
        Only authorized users can access password change page.
        """
        url = reverse('accounts:password_change')
        response = self.client.post(url, follow=True)
        next_url = reverse('accounts:login') + '?next=' + url
        self.assertRedirects(response, next_url)
        self.assertContains(response, "Please login to see this page.")

    def test_password_change_success(self):
        """
        User's password is successfully updated.
        """
        self.register_user()
        new_user = USER_MODEL.objects.get()
        url = reverse('accounts:password_change')
        self.assertFalse(new_user.check_password(self.NEW_PASSWORD))

        response = self.client.post(
            url, self.get_password_change_dict(), follow=True)
        self.no_error_msgs(response)
        new_user = USER_MODEL.objects.get()
        self.assertTrue(new_user.check_password(self.NEW_PASSWORD))

    def test_changed_password_logged_in(self):
        """
        Changing the password doesn't log the user out.
        """
        self.register_user()
        url = reverse('accounts:password_change')

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        self.client.post(url, self.get_password_change_dict(), follow=True)

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_all_fields_provided(self):
        """
        All 3 fields return an error if missing.
        """
        self.register_user()
        url = reverse('accounts:password_change')

        full_form = self.get_password_change_dict()
        form_to_post = {}

        fields_list = list(self.get_password_change_dict())
        fields_dict = {
            'errors': fields_list.copy(),
            'clean': []
        }
        for field in fields_list:
            response = self.client.post(url, form_to_post, follow=True)
            for item in fields_dict['errors']:
                self.assertTrue(item in response.context['form'].errors)
            for item in fields_dict['clean']:
                self.assertFalse(item in response.context['form'].errors)
            form_to_post[field] = full_form[field]
            fields_dict['errors'].remove(field)
            fields_dict['clean'].append(field)

        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)

        new_user = USER_MODEL.objects.get()
        self.assertTrue(new_user.check_password(self.NEW_PASSWORD))

    def test_old_password_correct(self):
        """
        Return an error if old password is not correct.
        """
        self.register_user()
        url = reverse('accounts:password_change')

        form_to_post = self.get_password_change_dict()
        form_to_post['old_password'] = form_to_post['old_password'] + '1'
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('old_password' in response.context['form'].errors)
        new_user = USER_MODEL.objects.get()
        self.assertTrue(
            new_user.check_password(self.user_for_tests['password1']))

        form_to_post['old_password'] = self.user_for_tests['password1']
        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)
        new_user = USER_MODEL.objects.get()
        self.assertTrue(new_user.check_password(self.NEW_PASSWORD))

    def test_new_password_no_match(self):
        """
        Return an error if new password and cofnirmation don't match.
        """
        self.register_user()
        url = reverse('accounts:password_change')

        form_to_post = self.get_password_change_dict()
        form_to_post['new_password2'] = form_to_post['new_password2'] + '1'
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('new_password2' in response.context['form'].errors)
        new_user = USER_MODEL.objects.get()
        self.assertTrue(
            new_user.check_password(self.user_for_tests['password1']))

        form_to_post['new_password2'] = form_to_post['new_password1']
        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)
        new_user = USER_MODEL.objects.get()
        self.assertTrue(new_user.check_password(self.NEW_PASSWORD))

    def test_new_password_validation(self):
        """
        Password is rejected if it doesn't meet requirements.
        """
        # TODO


class LogoutViewTests(AccountsTestCase):

    def test_logout_authorized_user(self):
        """
        Logout view logs out authorized users.
        """
        self.register_user()
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

        url = reverse('accounts:logout')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))

        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

    def test_logout_anon_users_login(self):
        """
        Anonymous users accessing logout view are redirected to login page.
        """
        url = reverse('accounts:logout')
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, reverse('accounts:login'))
