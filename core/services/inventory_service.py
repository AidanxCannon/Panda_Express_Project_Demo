from django.db import transaction, models
from core.models import Inventory

class InventoryService:

    @staticmethod
    def get_all_items():
        """Return all inventory items, sorted alphabetically."""
        return Inventory.objects.order_by("ingredient").all()

    @staticmethod
    def add_item(name, quantity, price, minimum_stock=None):
        """Insert new item."""
        item = Inventory(
            ingredient=name,
            quantity=quantity,
            price=price,
            minimum_stock=minimum_stock,
        )
        item.save()
        return item

    @staticmethod
    def update_item(original_name, new_name=None, new_price=None, new_quantity=None, new_min_stock=None):
        """Update an existing item by ingredient name."""
        try:
            item = Inventory.objects.get(ingredient=original_name)
        except Inventory.DoesNotExist:
            return False

        if new_name is not None:
            item.ingredient = new_name
        if new_price is not None:
            item.price = new_price
        if new_quantity is not None:
            item.quantity = new_quantity
        if new_min_stock is not None:
            item.minimum_stock = new_min_stock

        item.save()
        return True

    @staticmethod
    def remove_item(name):
        """Delete an item."""
        deleted_rows, _ = Inventory.objects.filter(ingredient=name).delete()
        return deleted_rows == 1

    @staticmethod
    def add_quantity(name, delta):
        """Add (or subtract) from the quantity of an item."""
        updated_rows = Inventory.objects.filter(ingredient=name).update(
            quantity=models.F("quantity") + delta
        )
        return updated_rows == 1
