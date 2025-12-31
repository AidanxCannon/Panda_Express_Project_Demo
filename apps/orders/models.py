from django.db import models

class Employee(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    role = models.CharField(max_length=50)
    date_of_hire = models.DateField()
    password = models.CharField(max_length=255)

    class Meta:
        db_table = "employees"  
        managed = False          

    def __str__(self):
        return self.name


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    price = models.FloatField()
    time = models.DateTimeField()
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        db_column="employee_id"
    )

    class Meta:
        db_table = "orders"
        managed = False

    def __str__(self):
        return f"Order #{self.id} - ${self.price} at {self.time}"


class RecipeOrder(models.Model):
    id = models.AutoField(primary_key=True)
    recipe_id = models.IntegerField()
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column="order_id"
    )

    class Meta:
        db_table = "recipe_orders"
        managed = False

    def __str__(self):
        return f"RecipeOrder #{self.id} for Order #{self.order.id}"
