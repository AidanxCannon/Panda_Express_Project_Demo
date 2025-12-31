"""Utility model for the customer kiosk.
"""

from django.db import models


class CustomerItem(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        # Bind to the existing ``recipes`` table.  Setting ``managed = False``
        db_table = "recipes"
        managed = False

    def __str__(self) -> str:
        # Represent the item with its name and price for convenient display.
        return f"{self.name} (${self.price})"