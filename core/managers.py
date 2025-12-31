"""
Manager classes for business logic and database operations.
"""
from typing import Optional, List
from datetime import date
from .models import Employee


class ManageEmployees:
    """
    Manager for handling Employee database operations.
    Uses Django ORM instead of raw SQL connections.
    """
    
    # Field name constants (for reference/documentation)
    TABLE_EMPLOYEES = "employees"
    FIELD_EMP_ID = "id"
    FIELD_EMP_NAME = "name"
    FIELD_ROLE = "role"
    FIELD_PASSWORD = "password"
    FIELD_DATE_OF_BIRTH = "date_of_birth"
    FIELD_DATE_OF_HIRE = "date_of_hire"
    
    def __init__(self):
        """
        Default constructor.
        Note: Django ORM handles database connections automatically.
        """
        print("[DEBUG] ManageEmployees initialized with Django ORM")
    
    def add_employee(self, name: str, role: str, password: str, 
                    dob: date, doh: date) -> Optional[int]:
        """
        Adds a new employee to the database.
        
        @param name The employee's full name
        @param role The employee's role (e.g., "Manager", "Cashier")
        @param password The employee's login password
        @param dob The employee's date of birth
        @param doh The employee's date of hire
        @return The new employee's ID, or None if the operation failed
        """
        try:
            employee = Employee.objects.create(
                name=name,
                role=role,
                password=password,
                date_of_birth=dob,
                date_of_hire=doh
            )
            return employee.id
        except Exception as e:
            raise RuntimeError(f"Add employee failed: {e}")
    
    def update_employee(self, emp_id: int, name: str, role: str, 
                       dob: Optional[date], doh: Optional[date]) -> int:
        """
        Updates an existing employee's information.
        
        @param emp_id The ID of the employee to update
        @param name The employee's new name
        @param role The employee's new role
        @param dob The employee's new date of birth
        @param doh The employee's new date of hire
        @return Number of rows affected (should be 1 if successful)
        """
        try:
            rows_updated = Employee.objects.filter(id=emp_id).update(
                name=name,
                role=role,
                date_of_birth=dob,
                date_of_hire=doh
            )
            return rows_updated
        except Exception as e:
            raise RuntimeError(f"Update employee failed: {e}")
    
    def remove_employee(self, emp_id: int) -> int:
        """
        Removes an employee from the database.
        
        @param emp_id The ID of the employee to remove
        @return Number of rows affected (should be 1 if successful)
        """
        try:
            rows_deleted, _ = Employee.objects.filter(id=emp_id).delete()
            return rows_deleted
        except Exception as e:
            raise RuntimeError(f"Remove employee failed: {e}")
    
    def change_password(self, emp_id: int, new_pass: str) -> int:
        """
        Changes an employee's password.
        
        @param emp_id The ID of the employee
        @param new_pass The new password
        @return Number of rows affected (should be 1 if successful)
        """
        try:
            rows_updated = Employee.objects.filter(id=emp_id).update(
                password=new_pass
            )
            return rows_updated
        except Exception as e:
            raise RuntimeError(f"Change password failed: {e}")
    
    def get_all_employees(self) -> List[Employee]:
        """
        Fetches all employees from the database.
        
        @return A list of Employee objects
        """
        try:
            employees = list(Employee.objects.all().order_by('name'))
            print(f"[DEBUG] Loaded {len(employees)} employees")
            return employees
        except Exception as e:
            raise RuntimeError(f"Fetch employees failed: {e}")
    
    def authenticate(self, name: str, password: str) -> Optional[Employee]:
        """
        Authenticates an employee login with name and password.
        
        @param name The employee name
        @param password The password to verify
        @return Employee object if authentication succeeds, None otherwise
        """
        try:
            employee = Employee.objects.filter(
                name=name,
                password=password
            ).first()
            return employee
        except Exception as e:
            raise RuntimeError(f"Authentication failed: {e}")
