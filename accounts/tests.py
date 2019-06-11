from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.db import utils

from datetime import date

from .helpers import AccountsTestConstants

USER_MODEL = get_user_model()


class UserModelTests(TestCase, AccountsTestConstants):

    def test_user_created(self):
        """
        User is created using create_user()
        """
        user_dict = self.user_for_create_user
        new_user = self.create_test_user()
        self.assertEqual(new_user, USER_MODEL.objects.get())
        self.assertTrue(new_user.check_password(user_dict.pop('password')))
        self.assert_single_user_fields(user_dict)

    def test_superuser_created(self):
        """
        Superuser is created using create_superuser()
        """
        user_dict = self.user_for_create_user
        new_superuser = USER_MODEL.objects.create_superuser(**user_dict)
        self.assertEqual(new_superuser, USER_MODEL.objects.get())
        self.assertTrue(USER_MODEL.objects.get().is_admin)
        self.assertTrue(
            new_superuser.check_password(user_dict.pop('password')))
        self.assert_single_user_fields(user_dict)

    def test_guest_user_created(self):
        """
        Guest user is created using create_guest_user()
        which doesn't require password.
        """
        new_guest_user = self.create_test_guest_user()
        self.assertEqual(new_guest_user, USER_MODEL.objects.get())
        self.assertTrue(USER_MODEL.objects.get().is_guest)

    def test_user_superuser_require_password(self):
        """
        Unlike guest user, user and superuser require password.
        """
        user = self.user_for_create_user
        user['password'] = None
        with self.assertRaises(ValueError):
            USER_MODEL.objects.create_user(**user)
        with self.assertRaises(ValueError):
            USER_MODEL.objects.create_superuser(**user)

    def test_user_not_allowed_duplicate_number_email(self):
        """
        Users are not allowed to have a phone_number or an email
        which are already registered.
        """
        user_dict = self.user_for_create_user
        USER_MODEL.objects.create_user(**user_dict)

        self.assert_db_value_error_in_create(user_dict)

        orig_email = user_dict['email']
        user_dict['email'] = "1" + user_dict['email']
        self.assert_db_value_error_in_create(user_dict)

        user_dict['email'] = orig_email
        user_dict['phone_number'] = "1" + user_dict['phone_number']
        self.assert_db_value_error_in_create(user_dict)

        user_dict['email'] = "1" + user_dict['email']
        try:
            USER_MODEL.objects.create_user(**user_dict)
        except (utils.IntegrityError, ValueError):
            raise AssertionError

    def test_user_duplicate_guest_number_email(self):
        """
        Users are allowed to have
        a phone number and an email which were already used by other guest.
        """
        self.create_test_guest_user()

        user_dict = self.user_for_create_user
        try:
            USER_MODEL.objects.create_user(**user_dict)
        except (utils.IntegrityError, ValueError):
            raise AssertionError

        users = USER_MODEL.objects.all()
        self.assertEqual(users[0].phone_number, users[1].phone_number)
        self.assertEqual(users[0].email, users[1].email)

    def test_guest_user_duplicate_registered_number_email(self):
        """
        Guest users are allowed to have
        a phone number and an email which were already registered.
        """
        user_dict = self.user_for_create_user
        USER_MODEL.objects.create_user(**user_dict)

        try:
            self.create_test_guest_user()
        except (utils.IntegrityError, ValueError):
            raise AssertionError

        users = USER_MODEL.objects.all()
        self.assertEqual(users[0].phone_number, users[1].phone_number)
        self.assertEqual(users[0].email, users[1].email)

    def test_guest_user_duplicate_guest_number_email(self):
        """
        Guest users are allowed to have
        a phone number and an email which were already used by other guest.
        """
        first_guest_user = self.create_test_guest_user()
        second_guest_user = self.create_test_guest_user()
        self.assertNotEqual(first_guest_user, second_guest_user)


class AccountsTestCase(TestCase, AccountsTestConstants):

    """
    Methods for tests.
    """

    def register_user(self, user=None):
        """
        POST a register form.
        """
        user = user or self.user_for_tests.copy()
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
        self.assertFalse(USER_MODEL.objects.all().exists())
        for field in self.required_fields:
            response = self.client.post(url, form_to_post, follow=True)

            self.assertTrue(field in response.context['form'].errors)
            self.assertContains(response, "This field is required")
            self.assertFalse(USER_MODEL.objects.all().exists())

            form_to_post[field] = self.user_for_tests[field]

        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue(USER_MODEL.objects.all().exists())

    def test_register_unrequired(self):
        """
        Unrequired fields are...unrequired.
        """
        # CharField can't be stored as NULL(None)
        APARTMENT_VALUE = ''

        url = reverse('accounts:register')
        user = self.required_fields_user
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

        second_user['email'] = f"another{first_user['email']}"
        response = self.client.post(url, second_user, follow=True)
        self.assertTrue('phone_number' in response.context['form'].errors)
        self.assertFalse('email' in response.context['form'].errors)

        second_user['phone_number'] = f'0{first_user["phone_number"]}'
        response = self.client.post(url, second_user, follow=True)
        self.no_error_msgs(response)

        self.assertEqual(len(USER_MODEL.objects.all()), 2)

    def test_phone_email_guest_used(self):
        """
        Allow to register if phone or email were previously used by guest.
        """
        self.create_test_guest_user()
        user = self.user_for_tests.copy()
        url = reverse('accounts:register')
        self.client.post(url, user, follow=True)

        users = USER_MODEL.objects.all()
        self.assertEqual(users[0].phone_number, users[1].phone_number)
        self.assertEqual(users[0].email, users[1].email)
        self.assertNotEqual(users[0].is_guest, users[1].is_guest)

    def test_register_success_logs_in(self):
        """
        Successful registration automatically logs the new user in.
        """
        user = auth.get_user(self.client)
        self.assertFalse(user.is_authenticated)

        self.register_user()
        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)


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

    def test_guests_can_not_login(self):
        """
        You can't log in with guest's credentials.
        """
        guest_user = self.create_test_guest_user()
        self.assertFalse(guest_user.has_usable_password())

        url = reverse('accounts:login')
        form_to_post = {
            'username': self.user_for_tests['email'],
            'password': self.user_for_tests['password1']
        }
        response = self.client.post(url, form_to_post, follow=True)
        self.assertNotEqual(response.context['form'].errors, {})
        user = auth.get_user(self.client)
        self.assertTrue(user.is_anonymous)


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
        next_url = reverse('accounts:login') + '?next=' + profile_url

        response = self.client.get(profile_url, follow=True)
        self.assertRedirects(response, next_url)

        self.register_user()
        response = self.client.get(profile_url, follow=True)
        with self.assertRaises(AssertionError):
            self.assertRedirects(response, next_url)

    def test_profile_displays_form(self):
        """
        Profile page displays a form similar to registration form
        but without passwords fields.
        """
        self.register_user()
        url = reverse('accounts:profile')
        response = self.client.get(url, follow=True)
        form_fields = list(response.context['form'].fields.keys())

        profile_page_fields = self.profile_page_fields
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
        for field in self.profile_page_fields:
            try:
                updated_user[field] = self.user_for_tests[field] + '1'
            except TypeError:
                # date field
                full_date = self.user_for_tests[field]
                new_full_date = {}
                for value in self.user_form_date_fields:
                    new_full_date[value] = getattr(full_date, value) + 1
                updated_user[field] = date(**new_full_date)

        self.client.post(url, updated_user, follow=True)
        response = self.client.get(url, follow=True)
        form_fields_w_values = response.context['form'].initial
        for k, v in form_fields_w_values.items():
            self.assertEqual(v, updated_user[k])

    def test_profile_update_empty(self):
        """
        Can not update profile with empty values in required fields.
        """
        self.register_user()
        url = reverse('accounts:profile')

        form_to_post = {}
        profile_fields = self.user_without_password_fields()
        for field in self.unrequired_fields:
            profile_fields.pop(field)

        for field in profile_fields:
            response = self.client.post(url, form_to_post, follow=True)

            self.assertTrue(field in response.context['form'].errors)
            self.assertContains(response, "This field is required")

            form_to_post[field] = self.user_for_tests[field]

        response = self.client.post(url, form_to_post, follow=True)
        self.no_error_msgs(response)

    def test_same_unique_profile_update(self):
        """
        Passing your own phone number and email doesn't raise errors.
        """
        self.register_user()
        url = reverse('accounts:profile')
        response = self.client.post(url, self.user_for_tests, follow=True)
        self.assertEqual(0, len(response.context['form'].errors))

    def test_profile_update_duplicate_phone_email(self):
        """
        Don't allow users to change their phone number or email
        to an already registered one.
        """
        self.register_user()

        second_user = self.user_for_tests.copy()
        second_phone = f"0{second_user['phone_number']}"
        second_user['phone_number'] = second_phone
        second_user['email'] = f"another{second_user['email']}"
        self.register_user(second_user)
        users = USER_MODEL.objects.all()

        url = reverse('accounts:profile')
        second_user['phone_number'] = self.user_for_tests['phone_number']
        response = self.client.post(url, second_user, follow=True)

        self.assertTrue('phone_number' in response.context['form'].errors)
        self.assertNotEqual(users[0].phone_number, users[1].phone_number)

        second_user['email'] = self.user_for_tests['email']
        response = self.client.post(url, second_user, follow=True)

        self.assertTrue('email' in response.context['form'].errors)
        self.assertTrue('phone_number' in response.context['form'].errors)
        self.assertNotEqual(users[0].email, users[1].email)
        self.assertNotEqual(users[0].phone_number, users[1].phone_number)

        second_user['phone_number'] = second_phone
        response = self.client.post(url, second_user, follow=True)

        self.assertTrue('email' in response.context['form'].errors)
        self.assertTrue('phone_number' not in response.context['form'].errors)
        self.assertNotEqual(users[0].email, users[1].email)


class PasswordChangeViewTests(AccountsTestCase):

    def test_password_change_login_required(self):
        """
        Only authorized users can access password change page.
        """
        url = reverse('accounts:password_change')
        response = self.client.post(url, follow=True)
        next_url = reverse('accounts:login') + '?next=' + url
        self.assertRedirects(response, next_url)

    def test_password_change_success(self):
        """
        User's password is successfully updated.
        """
        self.register_user()
        new_user = USER_MODEL.objects.get()
        url = reverse('accounts:password_change')
        self.assertFalse(new_user.check_password(self.NEW_PASSWORD))

        response = self.client.post(
            url, self.password_change_dict, follow=True)
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

        self.client.post(url, self.password_change_dict, follow=True)

        user = auth.get_user(self.client)
        self.assertTrue(user.is_authenticated)

    def test_all_fields_provided(self):
        """
        All 3 fields return an error if missing.
        """
        self.register_user()
        url = reverse('accounts:password_change')

        full_form = self.password_change_dict
        form_to_post = {}

        fields_list = list(self.password_change_dict)
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

        form_to_post = self.password_change_dict
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

        form_to_post = self.password_change_dict
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

    def not_test_new_password_validation(self):
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
