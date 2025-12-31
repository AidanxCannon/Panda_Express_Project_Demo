from django.urls import path

from . import views

app_name = "cashier"

urlpatterns = [
    path("", views.cashierInterface, name="home"),
]
