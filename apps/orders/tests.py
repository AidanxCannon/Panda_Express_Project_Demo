from django.test import TestCase


class OrdersSmokeTests(TestCase):
    def test_models_load(self):
        # Basic smoke test to ensure the orders app models can be imported
        try:
            from apps.orders.models import Employee, Order, RecipeOrder  # noqa: F401
        except Exception as exc:
            self.fail(f"Importing orders models failed: {exc}")
