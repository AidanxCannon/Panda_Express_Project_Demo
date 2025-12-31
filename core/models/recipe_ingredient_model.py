from django.db import models

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        "Recipe",
        on_delete=models.CASCADE,
        db_column="recipe_id"
    )

    ingredient = models.ForeignKey(
        "Inventory",
        on_delete=models.CASCADE,
        db_column="ingredient_id"
    )

    class Meta:
        db_table = "recipe_ingredient"
        managed = False
        unique_together = [['recipe', 'ingredient']]

    def __str__(self):
        return f"Recipe {self.recipe_id} - Ingredient {self.ingredient_id}"
