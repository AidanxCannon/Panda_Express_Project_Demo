from django.db import models


class Employee(models.Model):
    """
    Represents an employee record from the database.
    """
    # The unique identifier is automatically created by Django as 'id' (primary key)
    
    # The name of the employee
    name = models.CharField(max_length=100)
    
    # The date of birth of the employee
    date_of_birth = models.DateField()
    
    # The role or job title of the employee
    role = models.CharField(max_length=50)
    
    # The date the employee was hired
    date_of_hire = models.DateField()
    
    # The password associated with the employee account
    password = models.CharField(max_length=255)
    
    def __str__(self):
        """
        Returns a string representation of the employee, including ID, name, and role.
        
        @return a string representing the employee
        """
        return f"Employee{{id={self.id}, name='{self.name}', role='{self.role}'}}"
    
    class Meta:
        db_table = 'employees'  # Match the actual database table name
        managed = False  # Don't let Django manage this table (it already exists)

