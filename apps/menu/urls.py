from django.urls import path

from . import views

app_name = "menu"

urlpatterns = [
    path("", views.menu_board, name="home"),
    path("set-language/", views.cycle_language, name="set_lang"),
]
