from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date

EMAIL = 'test@example.com'
USER_MODEL = get_user_model()


class RegisterViewTests(TestCase):

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

    def register_user(self):
        """
        POST a register form.
        """
        # TODO

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
        Not required fields are stored if provided.
        """
        url = reverse('accounts:register')
        response = self.client.post(url, self.user_for_tests, follow=True)
        print(response.context['form'].errors)
        # print(USER_MODEL.objects.all())
        user = USER_MODEL.objects.get(pk=1).__dict__
        for field in self.unrequired_fields:
            self.assertEqual(user[field], self.user_for_tests[field])

    def test_register_standard_phone(self):
        """
        Provided phone number is standardized before saving.
        """
        # TODO


class LoginViewTests(TestCase):

    def test_login_empty(self):
        """
        Trying to log in with empty fields
        refreshes the page with an error message.
        """
        # TODO both fields empty and then password empty

    def test_login_incorrect(self):
        """
        Trying to log in with incorrect credentials
        refreshes the page with an error message.
        """
        # TODO

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


class ProfileViewTests(TestCase):

    # TODO
    pass


class ChangePasswordViewTests(TestCase):

    pass
    # TODO
