from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import Recipe, Order, RecipeOrder
import json


class CashierViewTests(TestCase):
    """Test suite for cashier view functions."""
    
    def setUp(self):
        """Set up test client and sample recipes."""
        self.client = Client()
        
        # Create sample recipes for testing
        self.side1 = Recipe.objects.create(
            name="Fried Rice",
            type="Side",
            price=0.00,
            active=True
        )
        self.side2 = Recipe.objects.create(
            name="Chow Mein",
            type="Side",
            price=0.00,
            active=True
        )
        self.entree1 = Recipe.objects.create(
            name="Orange Chicken",
            type="Entree",
            price=0.00,
            active=True
        )
        self.entree2 = Recipe.objects.create(
            name="Beijing Beef",
            type="Entree",
            price=0.00,
            active=True
        )
        self.appetizer = Recipe.objects.create(
            name="Chicken Egg Roll",
            type="Appetizer",
            price=1.50,
            active=True
        )
        self.drink = Recipe.objects.create(
            name="Coca Cola",
            type="Drink",
            price=2.00,
            active=True
        )
        # Inactive recipe should not appear
        self.inactive_recipe = Recipe.objects.create(
            name="Discontinued Item",
            type="Entree",
            price=0.00,
            active=False
        )
    
    def test_cashier_interface_loads_successfully(self):
        """Test that the cashier interface page loads with status 200."""
        response = self.client.get(reverse('cashier:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cashier/home.html')
    
    def test_cashier_interface_displays_active_recipes(self):
        """Test that only active recipes are displayed in the correct categories."""
        response = self.client.get(reverse('cashier:home'))
        
        # Check that active recipes are in context
        self.assertIn('sides', response.context)
        self.assertIn('entrees', response.context)
        self.assertIn('appetizers', response.context)
        self.assertIn('drinks', response.context)
        
        # Verify correct categorization
        sides = list(response.context['sides'])
        entrees = list(response.context['entrees'])
        appetizers = list(response.context['appetizers'])
        drinks = list(response.context['drinks'])
        
        self.assertEqual(len(sides), 2)
        self.assertEqual(len(entrees), 2)
        self.assertEqual(len(appetizers), 1)
        self.assertEqual(len(drinks), 1)
        
        # Verify inactive recipe is not included
        self.assertNotIn(self.inactive_recipe, entrees)
    
    def test_create_order_success(self):
        """Test successful order creation with multiple items."""
        order_data = {
            "orderItems": [
                {
                    "menuItemName": "Bowl",
                    "category": "bowl",
                    "recipes": [
                        {"id": str(self.side1.id), "name": "Fried Rice", "type": "Side"},
                        {"id": str(self.entree1.id), "name": "Orange Chicken", "type": "Entree"}
                    ],
                    "price": 8.30
                },
                {
                    "menuItemName": "Chicken Egg Roll",
                    "category": "appetizer",
                    "recipes": [
                        {"id": str(self.appetizer.id), "name": "Chicken Egg Roll", "type": "Appetizer"}
                    ],
                    "price": 1.50
                }
            ],
            "totalPrice": 9.80
        }
        
        response = self.client.post(
            reverse('cashier:home'),
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertIn('order_id', response_data)
        
        # Verify order was created in database
        order = Order.objects.get(id=response_data['order_id'])
        self.assertEqual(float(order.price), 9.80)
        self.assertIsNotNone(order.time)
    
    def test_create_order_empty_items(self):
        """Test that creating an order with no items returns an error."""
        order_data = {
            "orderItems": [],
            "totalPrice": 0.00
        }
        
        response = self.client.post(
            reverse('cashier:home'),
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'No items in order')
    
    def test_create_order_invalid_json(self):
        """Test that invalid JSON data returns appropriate error."""
        response = self.client.post(
            reverse('cashier:home'),
            data='invalid json data',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('Invalid JSON data', response_data['error'])
