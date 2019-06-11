from django.test import TestCase
from django.urls import reverse


class DeliveryViewsTests(TestCase):

    def assert_page_is_functional(self, name):
        """
        Check that page returns 200 and a template of the same name is used.
        """
        url = reverse(name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(f'{name}.html')

    def test_index_accessible(self):
        """
        Index page exists and can be accessed.
        """
        self.assert_page_is_functional('core:index')

    def test_delivery_accessible(self):
        """
        Delivery info page exists and can be accessed.
        """
        self.assert_page_is_functional('core:delivery')

    def test_info_accessible(self):
        """
        Company info page exists and can be accessed.
        """
        self.assert_page_is_functional('core:info')

    def test_contact_accessible(self):
        """
        Company contacts page exists and can be accessed.
        """
        self.assert_page_is_functional('core:contacts')
