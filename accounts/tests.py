from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date

EMAIL = 'test@example.com'
USER_MODEL = get_user_model()


class UserModelTests(TestCase):

    def test_user_created(self):
        """
        User is created using create_user()
        """
        new_user = USER_MODEL.objects.create_user(*("1" for i in range(6)))
        self.assertEqual(new_user, USER_MODEL.objects.get())

    def test_superuser_created(self):
        """
        Superuser is created using create_superuser()
        """
        new_superuser = USER_MODEL.objects.create_superuser(
            *("1" for i in range(6)))
        self.assertEqual(new_superuser, USER_MODEL.objects.get())
        self.assertTrue(USER_MODEL.objects.get().is_admin)


class AccountsTestCase(TestCase):

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
    login_form = {
        'phone_number': '12345',
        'password': 'testpassword'
    }
    phone_format_variations = ['+12345', '1(23)45', '123-45']

    def register_user(self):
        """
        POST a register form.
        """
        user = self.user_for_tests.copy()
        url = reverse('accounts:register')
        self.client.post(url, user, follow=True)


class RegisterViewTests(AccountsTestCase):

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
            self.assertFalse(field in response.context['form'].errors)
            try:
                next_field = self.required_fields[i+1]
            except IndexError:
                # all required fields are filled and user is registered
                self.assertEqual(len(USER_MODEL.objects.all()), 1)
            else:
                self.assertContains(response, "This field is required")
                self.assertTrue(next_field in response.context['form'].errors)

    def test_register_unrequired(self):
        """
        Unrequired fields are...unrequired.
        """
        url = reverse('accounts:register')
        user = self.user_for_tests.copy()
        for field in self.unrequired_fields:
            user.pop(field)
        self.client.post(url, user, follow=True)
        new_user = USER_MODEL.objects.get()
        for field in self.unrequired_fields:
            field_value = getattr(new_user, field)
            self.assertTrue(field_value in (None, ''))

    def test_register_unrequired_stored(self):
        """
        Unrequired fields are stored if provided.
        """
        url = reverse('accounts:register')
        self.client.post(url, self.user_for_tests, follow=True)
        user = USER_MODEL.objects.get()
        for field in self.unrequired_fields:
            field_value = getattr(user, field)
            self.assertEqual(field_value, self.user_for_tests[field])

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
            self.assertEqual(added_user.phone_number, '12345')
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
        self.assertFalse('phone_number' in response.context['form'].errors)
        self.assertFalse('email' in response.context['form'].errors)

        self.assertEqual(len(USER_MODEL.objects.all()), 2)

    def test_register_success_logs_in(self):
        """
        Successful registration automatically logs the new user in.
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

        form_to_post['username'] = self.login_form['phone_number']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertFalse('username' in response.context['form'].errors)
        self.assertTrue('password' in response.context['form'].errors)

        form_to_post['password'] = self.login_form['password']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertRedirects(response, reverse('accounts:profile'))

    def test_login_incorrect(self):
        """
        Trying to log in with incorrect credentials
        refreshes the page with an error message.
        """
        self.register_user()
        url = reverse('accounts:login')

        form_to_post = {
            'username': self.login_form['phone_number'] + '1',
            'password': self.login_form['password'] + '1',
        }
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('__all__' in response.context['form'].errors)

        form_to_post['username'] = self.login_form['phone_number']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertTrue('__all__' in response.context['form'].errors)

        form_to_post['password'] = self.login_form['password']
        response = self.client.post(url, form_to_post, follow=True)
        self.assertRedirects(response, reverse('accounts:profile'))

    def test_login_with_various_phone_formats(self):
        """
        Provided phone number is formatted to pass if correct.
        """
        # TODO add hyphens, parentheses, pluses

    def test_login_with_email(self):
        """
        If user provided an email on registration,
        check his input against it and log in on success.
        """
        # TODO

    def test_email_case_indifferent(self):
        """
        Email is stored in lowercase and email provided to login
        converted to lowercase before verifying.
        """
        # TODO

    def test_login_next_redirect(self):
        """
        Redirected to login and logged in users
        proceed according to next parameter.
        """
        # TODO


class ProfileViewTests(TestCase):

    # TODO
    pass


class ChangePasswordViewTests(TestCase):

    pass
    # TODO
