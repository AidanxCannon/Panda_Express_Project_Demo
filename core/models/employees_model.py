from django.db import models

class Employee(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    date_of_hire = models.DateField(null=True, blank=True)

    # NOTE: This is stored plain-text in your DB.
    # You may later want to change this to hashed using Django's user model system.
    password = models.CharField(max_length=10)

    class Meta:
        db_table = "employees"
        managed = False  # We are mapping an existing table

    def __str__(self):
        return self.name
