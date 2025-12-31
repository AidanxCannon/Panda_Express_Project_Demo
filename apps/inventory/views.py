from django.shortcuts import render


def home(request):
    """Render an inventory placeholder."""
    return render(request, "inventory/home.html")
