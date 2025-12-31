import os
import sys
from pathlib import Path

# Add project root and 'apps' folder to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "apps"))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "panda_config.settings")

import django
django.setup()

# Import models from orders app
from orders.models import Employee, Order, RecipeOrder

# Display all employees
print("=== Employees ===")
for emp in Employee.objects.all():
    print(f"{emp.id}: {emp.name} ({emp.role})")

# Display all orders
print("\n=== Orders ===")
for order in Order.objects.all():
    employee_name = order.employee.name if order.employee else "No employee"
    print(f"Order #{order.id} - ${order.price} at {order.time} by {employee_name}")

# Display all recipe orders
print("\n=== Recipe Orders ===")
for ro in RecipeOrder.objects.all():
    print(f"RecipeOrder #{ro.id} for Order #{ro.order.id} - Recipe ID: {ro.recipe_id}")
