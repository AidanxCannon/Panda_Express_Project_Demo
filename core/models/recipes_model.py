from django.db import models

class Recipe(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)

    # recipe_ingredient junction table used here
    ingredients = models.ManyToManyField(
        "Inventory",
        through="RecipeIngredient",
        related_name="recipes"
    )

    class Meta:
        db_table = "recipes"
        managed = False
    
    def __str__(self):
        return f"{self.name} (${self.price})"

    @property
    def category_label(self):
        if self.id <= 14:
            return "Entree"
        if 15 <= self.id <= 18:
            return "Side"
        if 19 <= self.id <= 21:
            return "Appetizer"
        if 22 <= self.id <= 37:
            return "Drink"
        return self.type or "Misc"
