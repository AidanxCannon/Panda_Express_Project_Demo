# services/employee_service.py

from django.db import transaction
from core.models import Employee   # adjust to correct app name


class EmployeeService:

    @staticmethod
    @transaction.atomic
    def add_employee(name, role, password, dob, doh):
        """
        Mimics Java: addEmployee()
        Returns: new employee's ID
        """
        emp = Employee.objects.create(
            name=name,
            role=role,
            password=password,
            date_of_birth=dob,
            date_of_hire=doh,
        )
        return emp.id

    @staticmethod
    @transaction.atomic
    def update_employee(emp_id, name, role, dob, doh):
        """
        Mimics Java: updateEmployee()
        Returns: number of rows affected (always 1 if success)
        """
        rows = Employee.objects.filter(id=emp_id).update(
            name=name,
            role=role,
            date_of_birth=dob,
            date_of_hire=doh,
        )
        return rows  # 1 = success, 0 = failure

    @staticmethod
    @transaction.atomic
    def delete_employee(emp_id):
        """
        Mimics Java: removeEmployee()
        Returns: number of rows affected
        """
        rows, _ = Employee.objects.filter(id=emp_id).delete()
        return rows

    @staticmethod
    @transaction.atomic
    def change_password(emp_id, new_pass):
        """
        Mimics Java: changePassword()
        Returns: number of rows affected
        """
        return Employee.objects.filter(id=emp_id).update(password=new_pass)

    @staticmethod
    def get_all_employees():
        """
        Mimics Java: getAllEmployees()
        Returns: queryset/list of Employee objects
        """
        return Employee.objects.order_by("name")

    @staticmethod
    def authenticate(emp_id, password):
        """
        Mimics Java: authenticate()
        Returns Employee object or None
        """
        try:
            return Employee.objects.get(id=emp_id, password=password)
        except Employee.DoesNotExist:
            return None
