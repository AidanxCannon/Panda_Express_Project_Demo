from .models import Employee
from core.models import Inventory, Recipe, Order, RecipeOrder
from django.db import connection


class Utils:
    @staticmethod
    def ValidateEmployeeLogin(emp_name: str, password: str) -> bool:
        """
        Validates employee login credentials.
        
        @param emp_name The employee's name
        @param password The employee's password
        @return True if credentials are valid, False otherwise
        """

        # Use database query to validate credentials
        try:
            employee = Employee.objects.get(name=emp_name, password=password)
            # if role is inactive, return False
            print(employee.role)
            if employee.role == 'inactive':
                return False

            return True
        except Employee.DoesNotExist:
            return False
        
    @staticmethod
    def DecreaseInventoryForOrder(order) -> None:
        """
        Decreases inventory based on the ingredients in every recipe in the order.
        
        @param order The order containing recipes to decrease inventory for
        """
        # Get all recipe IDs associated with this order using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT recipe_id FROM recipe_orders WHERE order_id = %s",
                [order.id]
            )
            recipe_ids = [row[0] for row in cursor.fetchall()]
        
        # Process each recipe
        for recipe_id in recipe_ids:
            recipe = Recipe.objects.get(id=recipe_id)
            # Get all ingredients for this recipe
            for ingredient in recipe.ingredients.all():
                inventory_item = Inventory.objects.get(id=ingredient.id)
                # Decrease inventory quantity
                inventory_item.quantity -= 1
                inventory_item.save()

    @staticmethod
    def generate_fortune() -> str:
        """ Generates a random fortune from fortunes.txt file """
  
        import os
        import random
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fortunes_path = os.path.join(current_dir, 'fortunes.txt')
        try:
            with open(fortunes_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            return ""
        fortunes = [f.strip() for f in content.split(',') if f.strip()]
        if not fortunes:
            return ""

        return random.choice(fortunes)