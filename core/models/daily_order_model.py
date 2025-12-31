from django.db import models

class DailyOrder(models.Model):
    id = models.AutoField(primary_key=True)
    price = models.FloatField()
    time = models.DateTimeField()

    employee = models.ForeignKey(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        db_column="employee_id"
    )

    class Meta:
        db_table = "daily_orders"
        managed = False  # IMPORTANT: Django won't try to create/alter the table
    
    recipes = models.ManyToManyField(
        "Recipe",
        through="DailyRecipeOrder",
        related_name="daily_orders"
    )

    def __str__(self):
        return f"Daily Order #{self.id} - ${self.price} at {self.time}"
