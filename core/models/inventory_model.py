from django.db import models

class Inventory(models.Model):
    ingredient = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "inventory"
        managed = False

    def __str__(self):
        return self.ingredient
