# apps/orders/serializers.py
from rest_framework import serializers
from .models import Employee, Order, RecipeOrder

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['id', 'name', 'date_of_birth', 'role', 'date_of_hire', 'password']

class OrderSerializer(serializers.ModelSerializer):
    employee = EmployeeSerializer(read_only=True)  # Nested employee details

    class Meta:
        model = Order
        fields = ['id', 'price', 'time', 'employee']

class RecipeOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeOrder
        fields = ['id', 'recipe_id', 'order_id']
