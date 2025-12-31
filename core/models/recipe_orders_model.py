from django.db import models

class RecipeOrder(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        db_column="recipe_id"
    )

    order = models.ForeignKey(
        "Order",
        on_delete=models.CASCADE,
        db_column="order_id",
        related_name="core_recipe_orders",
    )

    class Meta:
        db_table = "recipe_orders"
        managed = False
        unique_together = [['recipe', 'order']]

    def __str__(self):
        return f"RecipeOrder - Recipe {self.recipe_id} / Order {self.order_id}"
