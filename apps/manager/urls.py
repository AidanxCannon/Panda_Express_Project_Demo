from django.urls import path
from . import views

app_name = "manager"

urlpatterns = [
    path("", views.home, name="home"),
    path("view/<str:tab>/", views.tab_view, name="tab_view"),
    
    # Menu Management
    path("add_item/", views.add_item, name="add_item"),
    path("delete_item/", views.delete_item, name="delete_item"),
    path("get_recipe/<int:recipe_id>/", views.get_recipe, name="get_recipe"),
    path("edit_item/", views.edit_item, name="edit_item"),
    
    # Employee Management
    path("employees/add/", views.add_employee, name="add_employee"),
    path("employees/update/", views.update_employee, name="update_employee"),
    path("employees/reset_password/", views.reset_password, name="reset_password"),
    path("employees/delete/", views.delete_employee, name="delete_employee"),
    
    # Reports
    path("product_usage/", views.product_usage_report, name="product_usage_report"),
    path("sales_report/", views.sales_report, name="sales_report"),
    path("x_report/", views.x_report, name="x_report"),
    path("z_report/", views.z_report, name="z_report"),
    
    # Inventory Management
    path("inventory/", views.inventory_page, name="inventory_page"),
    path("inventory/add/", views.add_inventory_item, name="add_inventory_item"),
    path("inventory/edit/", views.edit_inventory_item, name="edit_inventory_item"),
    path("inventory/add_quantity/", views.add_inventory_quantity, name="add_inventory_quantity"),
    path("inventory/delete/", views.delete_inventory_item, name="delete_inventory_item"),
]