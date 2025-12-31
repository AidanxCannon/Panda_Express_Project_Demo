"""
URL configuration for panda_config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from apps.cashier import views as cashier_views
from apps.homePage import views as home_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("cashierInterface/", cashier_views.cashierInterface, name="cashierInterface"),
    path(
        "cashierInterface/create-order/",
        cashier_views.create_order,
        name="create_order",
    ),
    path("", home_views.login, name="login"),
    path("home/", home_views.home, name="home"),
    path(
        "kiosk/",
        include(("apps.customer_kiosk.urls", "customer_kiosk"), namespace="customer_kiosk"),
    ),
    path(
        "kiosk/",
        include(("apps.customer_kiosk.urls", "kiosk"), namespace="kiosk"),
    ),
    path(
        "cashier/",
        include(("apps.cashier.urls", "cashier"), namespace="cashier"),
    ),
    path(
        "kitchen/",
        include(("apps.kitchen.urls", "kitchen"), namespace="kitchen"),
    ),
    path(
        "manager/",
        include(("apps.manager.urls", "manager"), namespace="manager"),
    ),
    path(
        "menu/",
        include(("apps.menu.urls", "menu"), namespace="menu"),
    ),
    path(
        "inventory/",
        include(("apps.inventory.urls", "inventory"), namespace="inventory"),
    ),
    path(
        "kitchen/queue/",
        TemplateView.as_view(template_name="kitchen/queue.html"),
        name="kitchen_queue",
    ),
]

# Serve /static/* in development when using Daphne
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
