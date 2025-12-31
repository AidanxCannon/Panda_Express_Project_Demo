from django.db import models

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    price = models.FloatField()
    time = models.DateTimeField()

    # add status column mapping to DB "status"
    status = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        db_column="status",
        default="pending",
    )

    employee = models.ForeignKey(
        "Employee",
        on_delete=models.SET_NULL,
        null=True,
        db_column="employee_id",
    )
    
    recipes = models.ManyToManyField(
        "Recipe",
        through="RecipeOrder",
        related_name="orders",
    )

    # helper to set status and save only that column
    def set_status(self, value):
        self.status = value
        self.save(update_fields=["status"])

    @property
    def is_completed(self):
        return (self.status or "").lower() in ("done", "completed", "complete", "ready", "fulfilled")

    class Meta:
        db_table = "orders"
        managed = False

    def __str__(self):
        return f"Order #{self.id} - ${self.price} at {self.time}"
