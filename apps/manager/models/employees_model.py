from django.db import models

# Employee data

# Employees table
class Employee(models.Model):
    name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=255, blank=True)
    date_of_hire = models.DateField(null=True, blank=True)
    password = models.CharField(max_length=10, blank=True)

    class Meta:
        db_table = 'employees'
        managed = True  # read-only

    def __str__(self):
        return self.name
