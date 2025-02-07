from django.test import TestCase
from django.urls import reverse


class PopularListViewTestCase(TestCase):
    def test_popular_list_status_code(self):
        response = self.client.get(reverse("main:popular_list"))
        self.assertEqual(response.status_code, 200)
