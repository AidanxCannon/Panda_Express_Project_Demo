# recipes_model.py
from django.db import models

class Recipe(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'recipes'
        managed = False

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe_id = models.IntegerField()
    ingredient_id = models.IntegerField()

    class Meta:
        db_table = 'recipe_ingredient'
        managed = False

    def save(self, *args, **kwargs):
        """
        Override save() to insert without an 'id' column.
        """
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(
                'INSERT INTO recipe_ingredient (recipe_id, ingredient_id) VALUES (%s, %s)',
                [self.recipe_id, self.ingredient_id]
            )


class Inventory(models.Model):
    ingredient = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'inventory'
        managed = True

    def __str__(self):
        return self.ingredient