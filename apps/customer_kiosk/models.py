"""Minimal kiosk menu model used for future expansion."""
from django.db import models  # type: ignore


class MenuItem(models.Model):
    """A simple model to represent a menu item.

    This model isn't strictly required for the ordering flow implemented
    here, but it's defined to showcase how you might persist menu items
    in a database for future expansion (e.g., editing prices in the admin).
    """

    CATEGORY_CHOICES = [
        ('side', 'Side'),
        ('entree', 'Entree'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.name} ({self.category}) - ${self.price}"
