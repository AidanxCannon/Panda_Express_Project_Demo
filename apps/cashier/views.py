from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import connection
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
from types import SimpleNamespace

# import the Recipe model from the project's models package
from core.models import Recipe, Order, RecipeOrder

from core import utils

# Image mapping reused from kiosk for visual parity
IMAGE_FILENAME_MAP = {
    "Beijing Beef": "kiosk/images/Beef_BeijingBeef.png",
    "Broccoli Beef": "kiosk/images/Beef_BroccoliBeef.png",
    "Black Pepper Chicken": "kiosk/images/Chicken_BlackPepperChicken.png",
    "Grilled Teriyaki Chicken": "kiosk/images/Chicken_GrilledTeriyakiChicken.png",
    "Kung Pao Chicken": "kiosk/images/Chicken_KungPaoChicken.png",
    "Mushroom Chicken": "kiosk/images/Chicken_MushroomChicken.png",
    "Honey Sesame Chicken Breast": "kiosk/images/ChickenBreast_HoneySesameChickenBreast.png",
    "String Bean Chicken Breast": "kiosk/images/ChickenBreast_StringBeanChickenBreast.png",
    "Honey Walnut Shrimp": "kiosk/images/Seafood_HoneyWalnutShrimp.png",
    "Original Orange Chicken": "kiosk/images/Chicken_OrangeChicken.png",
    "Hot Orange Chicken": "kiosk/images/spicy_orange_chicken.jpg",
    "SweetFire Chicken Breast": "kiosk/images/sweet_fire_chickenbreast.jpg",
    "Eggplant Tofu": "kiosk/images/eggplant_tofu.jpg",
    "Black Pepper Sirloin Steak": "kiosk/images/Beef_ShanghaiAngusSteak.png",
    "Chow Mein": "kiosk/images/Sides_ChowMein.png",
    "Fried Rice": "kiosk/images/Sides_FriedRice.png",
    "Super Greens": "kiosk/images/Vegetables_SuperGreens.png",
    "White Steamed Rice": "kiosk/images/Sides_WhiteSteamedRice.png",
    "Brown Steamed Rice": "kiosk/images/Sides_BrownSteamedRice.png",
    # Drinks
    "Coca Cola": "kiosk/images/drinks/coca_cola.png",
    "Diet Coke": "kiosk/images/drinks/diet_coke.png",
    "Dr Pepper": "kiosk/images/drinks/dr_pepper.png",
    "Sprite": "kiosk/images/drinks/sprite.png",
    "Minute Maid Lemonade": "kiosk/images/drinks/minute_maid_lemonade.png",
    "Watermelon Mango Refresher": "kiosk/images/drinks/watermelon_mango_refresher.png",
    "Peach Lychee Flavored Refresher": "kiosk/images/drinks/peach_lychee_refresher.png",
    "Mango Guava Flavored Tea": "kiosk/images/drinks/mango_guava_tea.png",
    # Appetizers
    "Chicken Egg Roll": "kiosk/images/appetizers/chicken_egg_roll.png",
    "Veggie Spring Roll": "kiosk/images/appetizers/veggie_spring_roll.png",
    "Cream Cheese Rangoon": "kiosk/images/appetizers/cream_cheese_rangoon.png",
    "Apple Pie Roll": "kiosk/images/appetizers/apple_pie_roll.png",
    "Chicken Potsticker": "kiosk/images/appetizers/chicken_potsticker.png",
}

# Pricing maps (reuse kiosk values)
ALA_CARTE_ITEMS = {
    'Orange Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Original Orange Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Hot Orange Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Grilled Teriyaki Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Beijing Beef': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Kung Pao Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Broccoli Beef': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Mushroom Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'Black Pepper Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'String Bean Chicken Breast': {'S': 5.40, 'M': 8.70, 'L': 11.40},
    'SweetFire Chicken Breast': {'S': 5.20, 'M': 8.50, 'L': 11.20},
    'Honey Walnut Shrimp': {'S': 6.90, 'M': 11.70, 'L': 15.90},
    'Black Pepper Sirloin Steak': {'S': 6.90, 'M': 11.70, 'L': 15.90},
    'Honey Sesame Chicken Breast': {'S': 5.40, 'M': 8.70, 'L': 11.40},
}
ALA_CARTE_SIZE_PRICES = {'S': 5.40, 'M': 8.70, 'L': 11.40}
ALA_CARTE_PREMIUM_SIZE_PRICES = {'S': 6.90, 'M': 11.70, 'L': 15.90}

APPETIZER_ITEMS = {
    'Chicken Egg Roll': {'S': 2.00, 'M': 6.00, 'L': 11.20},
    'Veggie Spring Roll': {'S': 2.00, 'M': 6.00, 'L': 11.20},
    'Cream Cheese Rangoon': {'S': 2.00, 'M': 6.00, 'L': 8.00},
    'Apple Pie Roll': {'S': 2.00, 'M': 6.20, 'L': 8.00},
    'Chicken Potsticker': {'S': 2.00, 'M': 6.00, 'L': 11.20},
}

DRINK_ITEMS = {
    'Coca Cola': {'S': 2.20, 'M': 2.40, 'L': 2.60},
    'Diet Coke': {'S': 2.20, 'M': 2.40, 'L': 2.60},
    'Dr Pepper': {'S': 2.20, 'M': 2.40, 'L': 2.60},
    'Sprite': {'S': 2.20, 'M': 2.40, 'L': 2.60},
    'Minute Maid Lemonade': {'S': 2.20, 'M': 2.40, 'L': 2.60},
    'Watermelon Mango Refresher': {'S': 2.40, 'M': 2.60, 'L': 3.00},
    'Peach Lychee Flavored Refresher': {'S': 2.40, 'M': 2.60, 'L': 3.00},
    'Mango Guava Flavored Tea': {'S': 2.40, 'M': 2.60, 'L': 3.00},
}
FOUNTAIN_DRINKS = {
    'Coca Cola',
    'Diet Coke',
    'Dr Pepper',
    'Sprite',
    'Minute Maid Lemonade',
}


def _with_images(queryset):
    """Attach image attribute to recipes when available."""
    enriched = []
    for item in queryset:
        item.image = IMAGE_FILENAME_MAP.get(getattr(item, "name", ""), None)
        enriched.append(item)
    return enriched

# Create your views here.
def cashierInterface(request):
    # Query active recipes and split by type
    # Use case-insensitive matching to be resilient to capitalization differences
    sides = _with_images(Recipe.objects.filter(active=True, type__iexact='Side'))
    entrees = _with_images(Recipe.objects.filter(active=True, type__iexact='Entree'))
    appetizers = _with_images(Recipe.objects.filter(active=True, type__iexact='Appetizer'))
    drinks = _with_images(Recipe.objects.filter(active=True, type__iexact='Drink'))

    # Pricing maps for front-end selection
    drink_price_map = {}
    drink_has_sizes = {}
    drink_single_price = {}
    for d in drinks:
        prices = DRINK_ITEMS.get(d.name)
        if prices:
            drink_price_map[d.name] = prices
            drink_has_sizes[d.name] = len(prices.keys()) > 1 or d.name in FOUNTAIN_DRINKS
            drink_single_price[d.name] = prices.get('M', list(prices.values())[0])
        else:
            base = float(getattr(d, "price", 0) or 0)
            drink_price_map[d.name] = {'M': base}
            drink_has_sizes[d.name] = d.name in FOUNTAIN_DRINKS
            drink_single_price[d.name] = base

    appetizer_price_map = {}
    for a in appetizers:
        prices = APPETIZER_ITEMS.get(a.name)
        if prices:
            appetizer_price_map[a.name] = prices
        else:
            base = float(getattr(a, "price", 0) or 0)
            appetizer_price_map[a.name] = {'S': base, 'M': base, 'L': base}

    alacarte_price_map = {}
    premium_items = set()
    for e in entrees:
        prices = ALA_CARTE_ITEMS.get(e.name)
        if prices:
            alacarte_price_map[e.name] = prices
            if prices.get('S', 0) >= ALA_CARTE_PREMIUM_SIZE_PRICES.get('S', 0):
                premium_items.add(e.name)
        else:
            base = float(getattr(e, "price", 0) or 0)
            if base <= 0:
                # Fallback to standard a la carte pricing when no explicit price is set
                alacarte_price_map[e.name] = dict(ALA_CARTE_SIZE_PRICES)
            else:
                alacarte_price_map[e.name] = {'S': base, 'M': base, 'L': base}

    context = {
        'sides': sides,
        'entrees': entrees,
        'appetizers': appetizers,
        'drinks': drinks,
        'drink_price_map': drink_price_map,
        'drink_has_sizes_map': drink_has_sizes,
        'drink_single_price_map': drink_single_price,
        'appetizer_price_map': appetizer_price_map,
        'alacarte_price_map': alacarte_price_map,
        'alacarte_size_prices': ALA_CARTE_SIZE_PRICES,
        'alacarte_premium_prices': ALA_CARTE_PREMIUM_SIZE_PRICES,
        'alacarte_premium_items': list(premium_items),
    }

    return render(request, 'cashier/home.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    """
    Create a new order with associated recipes.
    Expects JSON payload with:
    {
        "orderItems": [
            {
                "menuItemName": "Bowl",
                "category": "bowl",
                "recipes": [
                    {"id": "1", "name": "Fried Rice", "type": "Side"},
                    {"id": "5", "name": "Orange Chicken", "type": "Entree"}
                ],
                "price": 0.00
            },
            ...
        ],
        "totalPrice": 0.00
    }
    """
    try:

        # Parse the JSON data from request body
        data = json.loads(request.body)
        order_items = data.get('orderItems', [])
        total_price = data.get('totalPrice', 0.00)
        
        if not order_items:
            return JsonResponse({
                'success': False,
                'error': 'No items in order'
            }, status=400)
        
        # Create the Order
        order = Order.objects.create(
            price=total_price,
            time=timezone.now(),
            employee=None  # You can set this to the logged-in employee later
        )
        
        # Collect all recipe IDs from all menu items
        recipe_ids = []
        for item in order_items:
            for recipe in item.get('recipes', []):
                recipe_ids.append(recipe['id'])
        
        # Create RecipeOrder entries using raw SQL since table has no primary key
        with connection.cursor() as cursor:
            for recipe_id in recipe_ids:
                cursor.execute(
                    "INSERT INTO recipe_orders (recipe_id, order_id) VALUES (%s, %s)",
                    [recipe_id, order.id]
                )

        # Build cart structure identical to kiosk
        cart = []
        for item in order_items:
            category = item.get('category')
            name = item.get('menuItemName')
            price = item.get('price', 0.0)
            recipes = item.get('recipes', [])

            if category in ('bowl', 'plate', 'bigger-plate'):
                side = next((r['name'] for r in recipes if r.get('type') == 'Side'), None)
                entrees = [r['name'] for r in recipes if r.get('type') == 'Entree']
                cart.append({
                    'category': 'meal',
                    'meal_type': category,
                    'meal_name': name,
                    'side': side,
                    'entrees': entrees,
                    'price': price,
                })
            else:
                cart.append({
                    'category': category or 'item',
                    'name': name,
                    'size': None,
                    'price': price,
                })

        ''' Remove this notif, unnecessary 
        # WebSocket notify kitchen (same shape as kiosk)
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            try:
                async_to_sync(channel_layer.group_send)(
                    "orders",
                    {
                        "type": "order.update",
                        "message": {
                            "items": cart,
                            "total": total_price,
                        },
                    },
                )
            except Exception:
                pass
        '''
            
        # Decrease inventory for the order
        utils.Utils.DecreaseInventoryForOrder(order)

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': f'Order #{order.id} created successfully!'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

