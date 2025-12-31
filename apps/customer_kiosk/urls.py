"""URL routes for the customer self-service kiosk."""
from django.urls import path  # type: ignore

from . import views


app_name = 'customer_kiosk'

urlpatterns = [
    path('', views.home, name='home'),
    path('choose_side/<str:meal_type>/', views.choose_side, name='choose_side'),
    path('choose_entrees/<str:meal_type>/', views.choose_entrees, name='choose_entrees'),
    path('api/cart/add/', views.add_to_cart_api, name='api_add_to_cart'),
    # Additional ordering categories
    path('a-la-carte/', views.choose_a_la_carte, name='a_la_carte'),
    path('appetizers/', views.choose_appetizer, name='appetizers'),
    path('drinks/', views.choose_drink, name='drinks'),
    path('cart/remove/<int:index>/', views.remove_from_cart, name='remove_from_cart'),

    # Cart summary
    path('cart/', views.cart_summary, name='cart'),
    path('order-confirmation/', views.order_confirmation, name='order_confirmation'),
    path('email-sent/', views.email_sent, name='email_sent'),
    path('receipt/<int:order_id>/', views.print_receipt, name='print_receipt'),
    path('set-email-flag/', views.set_email_flag, name='set_email_flag'),

    # Legacy review path for backward compatibility
    path('review/', views.cart_summary, name='review'),
]
