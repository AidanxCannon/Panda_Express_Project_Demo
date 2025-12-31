"""Defines the views for the kitchen app."""
from django.shortcuts import render
from core.models.orders_model import Order
import json
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.views.decorators.http import require_POST

def home(request):
    """Render kitchen queue screen when accessed by request, also fetching recent orders from database as JSON."""


    orders = [] 
    qs = Order.objects.prefetch_related("recipes").order_by("-time")[:10]

    for order in qs:
        items = []
        for recipe in order.recipes.all():
            items.append({
                "name": recipe.name,
                "category": recipe.category_label,
                "price": float(recipe.price),
            })

        orders.append({
            "id": order.id,
            "time": order.time.isoformat(),
            "employee_id": order.employee_id,
            "items": items,
            "status": order.status,
        })

    json_orders = json.dumps(orders)

    return render(request, "kitchen/queue.html", {"recent_orders": json_orders})

@require_POST
def order_status(request, order_id):
    """
    Sets up an endpoint for kitchen staff to update order status, using post requests with JSON payloads.
    400 Bad Request is returned for invalid JSON or missing status field.
    """

    try:
        payload = json.loads(request.body.decode() or "{}")
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    status = payload.get("status")
    if status is None:
        return HttpResponseBadRequest("Missing 'status'")

    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        raise Http404("Order not found")

    # persist status using model helper
    order.set_status(status)
    return JsonResponse({"success": True, "id": order_id, "status": order.status})