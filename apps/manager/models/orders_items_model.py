# orders_items_model.py
from django.db import models

class Order(models.Model):
    price = models.FloatField()
    time = models.DateTimeField()
    employee_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default='pending')

    class Meta:
        db_table = 'orders'
        managed = False

    def __str__(self):
        return f"Order #{self.id} - ${self.price}"


class OrderItem(models.Model):
    recipe_id = models.IntegerField()
    order_id = models.IntegerField()

    class Meta:
        db_table = 'recipe_orders'
        managed = False

    def __str__(self):
        return f"Order {self.order_id} - Recipe {self.recipe_id}"


class DailyOrderItem(models.Model):
    recipe_id = models.IntegerField()
    order_id = models.IntegerField()

    class Meta:
        db_table = 'recipe_orders_daily'
        managed = True

    def __str__(self):
        return f"Recipe {self.recipe_id} - Order {self.order_id}"
    
class OrderZHistory(models.Model):
    zreports = models.DateTimeField(auto_now_add=True, primary_key=True)

    class Meta:
        db_table = 'zreporthistory'
        managed = True

    def __str__(self):
        return f"{self.zreports}"

