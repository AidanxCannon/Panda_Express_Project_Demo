from django.db import transaction
from django.utils import timezone

from core.models import (
    Order,
    DailyOrder,
    RecipeOrder,
    DailyRecipeOrder,
    Employee,
    Recipe,
)

class OrderService:

    @staticmethod
    def record_order(employee_id: int, total: float, recipe_ids: list[int]):
        if not recipe_ids:
            raise ValueError("Order must contain at least one recipe.")

        now = timezone.now()

        with transaction.atomic():  # same as conn.setAutoCommit(false)
            # Insert into orders table
            order = Order.objects.create(
                price=total,
                time=now,
                employee_id=employee_id,
            )

            # Insert into daily_orders table
            daily_order = DailyOrder.objects.create(
                price=total,
                time=now,
                employee_id=employee_id,
            )

            # Insert into recipe_orders and recipe_orders_daily (junction tables)
            RecipeOrder.objects.bulk_create([
                RecipeOrder(recipe_id=recipe_id, order_id=order.id)
                for recipe_id in recipe_ids
            ])

            DailyRecipeOrder.objects.bulk_create([
                DailyRecipeOrder(recipe_id=recipe_id, order_id=daily_order.id)
                for recipe_id in recipe_ids
            ])

            return order.id
