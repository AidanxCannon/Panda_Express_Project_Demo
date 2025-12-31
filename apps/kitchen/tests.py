"""Defines the test cases for the kitchen app."""
from django.urls import reverse
import core.models.orders_model as orders_model
from django.test import TestCase, Client
import json 

from core.models.recipes_model import Recipe
class KitchenTests(TestCase):
    """Test cases for the kitchen app views and order status updates. """
    def setUp(self):
        """Setting up Django test client."""
        self.client = Client()

    def test_order_status_update(self):
        """Test updating order status via POST request, checking database persistence. 
        Creates a sample order, updates its status, and verifies the changes in the database.
        400 Bad Request is expected for invalid JSON or missing status field.
        """
        # Create a sample order
        order = orders_model.Order.objects.create(employee_id=1)
        order.recipes.add(Recipe.objects.create(name="Test Recipe"))

        # Update order status to 'in_progress'
        response = self.client.post(
            reverse('kitchen-order-status', args=[order.id]),
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'in_progress')

        # Update order status to 'completed'
        response = self.client.post(
            reverse('kitchen-order-status', args=[order.id]),
            data=json.dumps({'status': 'completed'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')

    def test_view_status(self): 
        """Ensure kitchen home view loads successfully. 
        returns 200 OK status.
        """
        response = self.client.get(reverse('kitchen:home'))
        self.assertEqual(response.status_code, 200)

    def test_order_status_get_not_allowed(self):
        """Ensure GET to the status endpoint is rejected (405).
        returns 405 Method Not Allowed status.
        """
        order = orders_model.Order.objects.create(employee_id=1)
        resp = self.client.get(reverse('kitchen-order-status', args=[order.id]))
        self.assertEqual(resp.status_code, 405)

    def test_invalid_json_returns_400(self):
        """Posting invalid JSON should return 400 Bad Request.
        tests posting malformed JSON to the order status endpoint, resulting in a 400 response.
        """
        order = orders_model.Order.objects.create(employee_id=1)
        resp = self.client.post(
            reverse('kitchen-order-status', args=[order.id]),
            data='not-a-json',
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)

    def test_missing_status_field_returns_400(self):
        """Posting without 'status' field should return 400 Bad Request.
        tests the order status endpoint with JSON missing the 'status' field, expecting a 400 response.
        """
        order = orders_model.Order.objects.create(employee_id=1)
        resp = self.client.post(
            reverse('kitchen-order-status', args=[order.id]),
            data=json.dumps({}),  # No 'status' field
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 400)