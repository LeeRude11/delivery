from django.test import TestCase
from django.urls import reverse

from .models import InfoViewTemplate


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


class InfoViewTests(TestCase):
    """
    Test for info urls.
    """

    def test_add_new_info_views(self):
        """
        Adding new models creates new info views.
        """
        NEW_VIEW = 'new_page'
        url = reverse('core:info', args=(NEW_VIEW,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        InfoViewTemplate.objects.create(view_name=NEW_VIEW)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
