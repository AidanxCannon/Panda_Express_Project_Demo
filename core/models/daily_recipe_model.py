from django.db import models

class DailyRecipeOrder(models.Model):
    id = models.AutoField(primary_key=True)

    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        db_column="recipe_id"
    )

    daily_order = models.ForeignKey(
        "DailyOrder",
        on_delete=models.CASCADE,
        db_column="order_id"
    )

    class Meta:
        db_table = "recipe_orders_daily"
        managed = False

    def __str__(self):
        return f"DailyOrder {self.daily_order_id} -> Recipe {self.recipe_id}"
