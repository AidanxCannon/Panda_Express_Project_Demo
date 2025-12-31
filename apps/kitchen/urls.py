"""Defines the URL patterns for the kitchen app."""
from django.urls import path

from . import views

app_name = "kitchen"

urlpatterns = [
    path("", views.home, name="home"),
    path('api/orders/<int:order_id>/status/', views.order_status, name='kitchen-order-status'),
]
