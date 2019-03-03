from django.test import TestCase
from django.urls import reverse


class RegisterViewTests(TestCase):

    def test_register_empty(self):
        """
        Can not register with empty values in required fields.
        """
        # Phone, First name, Last name, Address are required.
        url = reverse('accounts:register')
        url
        """How do I post to register?"""

    def test_register_success(self):
        """
        Registration is success with required fields filled.
        """

    def test_register_email(self):
        """
        Email is not required, but is stored if provided.
        """


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


class ProfileViewTests(TestCase):

    pass


class ChangePasswordViewTests(TestCase):

    pass
