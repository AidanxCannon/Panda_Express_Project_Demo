"""Tests covering key customer kiosk view flows."""
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse


class CustomerKioskViewTests(TestCase):
    """Lightweight view tests for the customer kiosk flows."""

    def setUp(self):
        self.client = Client()
        # Avoid DB lookups inside the kiosk helpers; force the views to use fallback menus.
        for key in ("kiosk_sides", "kiosk_entrees", "kiosk_appetizers", "kiosk_drinks"):
            cache.set(key, [])

    def test_home_shows_meal_options(self):
        response = self.client.get(reverse("customer_kiosk:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kiosk/home.html")

        options = response.context.get("meal_options")
        self.assertIsNotNone(options)
        self.assertGreaterEqual(len(options), 3)
        self.assertTrue(all({"slug", "name", "price"} <= set(opt.keys()) for opt in options))

    def test_choose_side_valid_post_adds_meal_to_cart(self):
        url = reverse("customer_kiosk:choose_side", args=["bowl"])
        payload = {
            "sides": ["Fried Rice", "Chow Mein"],  # two halves for one required side
            "entree_qty_0": "1",  # first entree in fallback list
        }
        response = self.client.post(url, data=payload)
        self.assertEqual(response.status_code, 200)

        cart = self.client.session.get("cart", [])
        self.assertEqual(len(cart), 1)
        item = cart[0]
        self.assertEqual(item.get("category"), "meal")
        self.assertEqual(item.get("meal_type"), "bowl")
        self.assertEqual(item.get("meal_name"), "Bowl")
        self.assertEqual(item.get("entrees"), [{"name": "Orange Chicken", "qty": 1}])
        self.assertEqual(item.get("side"), [
            {"name": "Fried Rice", "qty": 0.5},
            {"name": "Chow Mein", "qty": 0.5},
        ])
        self.assertAlmostEqual(item.get("price"), 9.80, places=2)
        self.assertTrue(response.context.get("added"))

    def test_choose_side_invalid_selection_shows_error(self):
        url = reverse("customer_kiosk:choose_side", args=["plate"])
        # Missing required entrees and sides
        response = self.client.post(url, data={})
        self.assertEqual(response.status_code, 200)
        error = response.context.get("error")
        self.assertIsInstance(error, str)
        self.assertIn("Please select", error)
        self.assertEqual(self.client.session.get("cart", []), [])

    def test_cart_summary_recalculates_price_from_base(self):
        session = self.client.session
        session["cart"] = [{
            "category": "meal",
            "meal_type": "plate",
            "meal_name": "Plate",
            "side": [{"name": "Fried Rice", "qty": 1}],
            "entrees": [{"name": "Orange Chicken", "qty": 2}],
            "price": 0,  # will be overridden by view logic
        }]
        session.save()

        response = self.client.get(reverse("customer_kiosk:cart"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kiosk/cart.html")
        self.assertAlmostEqual(response.context.get("total"), 10.30, places=2)

        cart_entry = response.context.get("cart")[0]
        self.assertEqual(cart_entry.get("price"), 10.30)
        self.assertIn("with", cart_entry.get("selection_text", ""))

    def test_remove_from_cart_drops_item(self):
        session = self.client.session
        session["cart"] = [
            {"category": "drink", "name": "Coca Cola", "size": "M", "price": 2.40},
            {"category": "appetizer", "name": "Chicken Egg Roll", "size": "S", "price": 2.00},
        ]
        session.save()

        url = reverse("customer_kiosk:remove_from_cart", args=[0])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("customer_kiosk:cart"))

        cart = self.client.session.get("cart", [])
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["name"], "Chicken Egg Roll")

    def test_choose_drink_adds_item(self):
        url = reverse("customer_kiosk:drinks")
        payload = {"item": "Coca Cola", "size": "M"}
        response = self.client.post(url, data=payload, follow=True)
        self.assertRedirects(response, url)
        self.assertTrue(response.context.get("added"))

        cart = self.client.session.get("cart", [])
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["category"], "drink")
        self.assertEqual(cart[0]["name"], "Coca Cola")
        self.assertEqual(cart[0]["size"], "M")
        self.assertAlmostEqual(cart[0]["price"], 2.40, places=2)
