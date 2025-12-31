from datetime import datetime, date, timedelta
from django.db import transaction, connection
from django.db.models import Count, Sum, F
from django.utils import timezone

from core.models import (
    Inventory,
    Order,
    Recipe,
    RecipeOrder,
    DailyOrder,
    DailyRecipeOrder,
)


class AnalyticsService:

    @staticmethod
    def get_inventory_usage(start_time, end_time):
        """
        Django ORM equivalent of:
        SELECT ingredient, COUNT(*) as used_quantity, price ...
        """

        result = (
            Inventory.objects.filter(
                recipes__orders__time__range=(start_time, end_time)
            )
            .annotate(
                used_quantity=Count("recipes"),
            )
            .order_by("-used_quantity")
            .values("ingredient", "used_quantity", "price")
        )

        return list(result)

    @staticmethod
    def get_sales_report(start_time, end_time):
        """
        Django ORM equivalent of:
        SELECT recipe, COUNT(ro.id) AS quantity ...
        """
        result = (
            Recipe.objects.filter(
                orders__time__range=(start_time, end_time)
            )
            .annotate(quantity=Count("recipeorder"))
            .order_by("-quantity")
            .values("id", "name", "price", "type", "quantity")
        )

        return list(result)

    @staticmethod
    def get_x_report():
        """
        X-report = hourly sales totals for TODAY
        """
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        result = (
            DailyOrder.objects.filter(time__range=(start, end))
            .annotate(hour=F("time__hour"))
            .values("hour")
            .annotate(total=Sum("price"))
            .order_by("hour")
        )

        return {row["hour"]: float(row["total"]) for row in result}

    @staticmethod
    def get_z_report():
        """
        Z-report = X-report + DELETE rows from daily tables
        """

        z_report = AnalyticsService.get_x_report()

        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        with transaction.atomic():
            # Delete child records first
            DailyRecipeOrder.objects.filter(order__time__range=(start, end)).delete()
            DailyOrder.objects.filter(time__range=(start, end)).delete()

        return z_report

    @staticmethod
    def get_restock_report():
        """
        Django ORM equivalent of:
        SELECT ingredient, quantity, minimum_stock, price FROM inventory WHERE quantity <= minimum_stock
        """
        result = Inventory.objects.filter(
            quantity__lte=F("minimum_stock")
        ).order_by("ingredient").values("ingredient", "quantity", "price")

        return list(result)

    @staticmethod
    def add_seasonal_menu_item(name, type, price, ingredients: dict):
        """
        Inserts a new recipe + ingredient links.
        Equivalent to your seasonal DAO insert logic.
        """

        if not name or not type:
            raise ValueError("Name and type are required")

        with transaction.atomic():

            # Insert recipe
            recipe = Recipe.objects.create(name=name, price=price, type=type)

            # Loop through ingredient dict {"tomato": 2, "salt": 1}
            for ingredient_name, quantity in ingredients.items():
                ingredient_name = ingredient_name.strip()

                if not ingredient_name:
                    continue

                # Does ingredient exist?
                ingredient, created = Inventory.objects.get_or_create(
                    ingredient__iexact=ingredient_name,
                    defaults={"ingredient": ingredient_name, "quantity": 0, "minimum_stock": 0, "price": 0},
                )

                # Link recipe to ingredient (ManyToMany)
                recipe.ingredients.add(ingredient)

        return recipe.id
