from django.db import models

class MenuItem(models.Model):

    id = models.AutoField(primary_key=True)

    name = models.CharField(max_length=255)

    price = models.DecimalField(max_digits=10,decimal_places=2)
    type = models.CharField(max_length=50, blank=True, null=True)
    active = models.BooleanField(default=True)


    class Meta:
        db_table = "recipes"
        managed = False
    
    def __str__(self):
        return f"{self.name} (${self.price})"

