# apps/orders/views.py
from rest_framework import generics
from .models import Order, Employee, RecipeOrder
from serializers import OrderSerializer, EmployeeSerializer, RecipeOrderSerializer

# List all orders
class OrderListView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

# Retrieve a specific order by id
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

# List all employees
class EmployeeListView(generics.ListCreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

# Retrieve a specific employee
class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

# List all recipe orders
class RecipeOrderListView(generics.ListCreateAPIView):
    queryset = RecipeOrder.objects.all()
    serializer_class = RecipeOrderSerializer

# Retrieve a specific recipe order
class RecipeOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = RecipeOrder.objects.all()
    serializer_class = RecipeOrderSerializer
