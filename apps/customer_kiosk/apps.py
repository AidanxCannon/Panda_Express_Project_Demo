"""App configuration for the customer kiosk Django app."""
from django.apps import AppConfig  # type: ignore


class KioskConfig(AppConfig):
    """Configure kiosk app metadata for Django."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.customer_kiosk'
