"""Views and helpers powering the customer-facing self-order kiosk."""

from decimal import Decimal
from types import SimpleNamespace
import re

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.db import connection
from django.db.models import F
from django.http import HttpRequest, HttpResponse, JsonResponse  # type: ignore
from django.shortcuts import render, redirect  # type: ignore
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import logout as django_logout

from core.models import Inventory, Order, Recipe
from core.services.recipe_service import RecipeService
from core.services.azure_email_service import AzureEmailService
from core.utils import Utils
from apps.menu.translate import translate, translate_many, LANGUAGES


def _build_kiosk_ui(lang: str) -> dict:
    """Build a small dict of common kiosk UI strings translated to `lang`.

    Uses `translate_many` to minimize API calls and returns a mapping that
    templates can read from the `kiosk_ui` context key.
    """
    keys = [
        'Bowl', 'Plate', 'Bigger Plate', 'A La Carte', 'Appetizers', 'Drinks', 'Cart',
        'View Cart', 'Choose Language', 'Close', 'Choose a meal type', 'Tap to customize your meal',
        'Please select an item and size.', 'Please select exactly {n} entrée{p}.',
        'Sides', 'Entrees', 'Selected:', 'Use +/− to adjust quantity', 'Clear', 'Add to Cart', 'Save Changes', 'Cart Total:', 'Review Order', 'Items', 'Select one',
        'Order Confirmation', 'Thank you!', 'Your order has been received and is being processed. Please remember your order number for pickup.', 'Return to Menu', 'Print Receipt', 'Email Receipt',
        # Empty cart and quick actions
        'Your cart is empty. Browse the menu to start an order.', 'Browse Menu', 'Grab a Drink',
        # Cart action buttons
        'Continue Shopping', 'Purchase'
        # Size labels and helpers
        , 'Size', 'Pick one', 'Small', 'Medium', 'Large', 'Price:', 'one size'
    ]
    # Expand the pluralizable sample to reduce later calls; actual formatting
    # (like replacing {n}) will be done in views where needed.
    translations = translate_many(keys, lang) if lang != 'en' else {k: k for k in keys}
    ui = {
        'nav': {
            'bowl': translations.get('Bowl', 'Bowl'),
            'plate': translations.get('Plate', 'Plate'),
            'bigger_plate': translations.get('Bigger Plate', 'Bigger Plate'),
            'a_la_carte': translations.get('A La Carte', 'A La Carte'),
            'appetizers': translations.get('Appetizers', 'Appetizers'),
            'drinks': translations.get('Drinks', 'Drinks'),
            'cart': translations.get('Cart', 'Cart'),
        },
        'view_cart': translations.get('View Cart', 'View Cart'),
        'sections': {
            'sides': translations.get('Sides', 'Sides'),
            'entrees': translations.get('Entrees', 'Entrees'),
            'items': translations.get('Items', 'Items'),
        },
        'labels': {
            'selected': translations.get('Selected:', 'Selected:'),
            'qty_hint': translations.get('Use +/− to adjust quantity', 'Use +/− to adjust quantity'),
            'clear': translations.get('Clear', 'Clear'),
            'add_to_cart': translations.get('Add to Cart', 'Add to Cart'),
            'save_changes': translations.get('Save Changes', 'Save Changes'),
            'cart_total': translations.get('Cart Total:', 'Cart Total:'),
            'review_order': translations.get('Review Order', 'Review Order'),
            'browse_menu': translations.get('Browse Menu', 'Browse Menu'),
            'grab_drink': translations.get('Grab a Drink', 'Grab a Drink'),
            'continue_shopping': translations.get('Continue Shopping', 'Continue Shopping'),
            'purchase': translations.get('Purchase', 'Purchase'),
        },
        'lang_modal': {
            'title': translations.get('Choose Language', 'Choose Language'),
            'close': translations.get('Close', 'Close'),
        },
        'order': {
            'title': translations.get('Order Confirmation', 'Order Confirmation'),
            'thank_you': translations.get('Thank you!', 'Thank you!'),
            'description': translations.get('Your order has been received and is being processed. Please remember your order number for pickup.', 'Your order has been received and is being processed. Please remember your order number for pickup.'),
            'return_to_menu': translations.get('Return to Menu', 'Return to Menu'),
            'print_receipt': translations.get('Print Receipt', 'Print Receipt'),
            'email_receipt': translations.get('Email Receipt', 'Email Receipt'),
        },
        'home': {
            'title': translations.get('Choose a meal type', 'Choose a meal type'),
            'hint': translations.get('Tap to customize your meal', 'Tap to customize your meal'),
        },
        'size': {
                'title': translations.get('Size', 'Size'),
                'pick_one': translations.get('Pick one', 'Pick one'),
            'sizes': {
                'S': translations.get('Small', 'Small'),
                'M': translations.get('Medium', 'Medium'),
                'L': translations.get('Large', 'Large'),
            },
                'price_label': translations.get('Price:', 'Price:'),
                'one_size': translations.get('one size', 'one size'),
        },
        'defaults': translations,
        'empty': {
            'empty_copy': translations.get('Your cart is empty. Browse the menu to start an order.', 'Your cart is empty. Browse the menu to start an order.'),
        },
    }
    return ui


def _translate_items_in_list(items: list, lang: str, name_key: str = 'name'):
    """Add `translated_name` to each mapping/object in `items` using `name_key`."""
    names = [getattr(i, name_key, None) if not isinstance(i, dict) else i.get(name_key) for i in items]
    # normalize
    names = [n for n in names if n]
    if not names or lang == 'en':
        for it in items:
            if isinstance(it, dict):
                it['translated_name'] = it.get(name_key)
            else:
                setattr(it, 'translated_name', getattr(it, name_key, None))
        return
    mapping = translate_many(names, lang)
    for it in items:
        if isinstance(it, dict):
            it['translated_name'] = mapping.get(it.get(name_key), it.get(name_key))
        else:
            setattr(it, 'translated_name', mapping.get(getattr(it, name_key, None), getattr(it, name_key, None)))
# Map menu item names to static image filenames.
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


# Simple price structure based on Panda Express menu as of 2025【280186582856260†L86-L125】
MEAL_PRICES = {
    'bowl': 9.80,
    'plate': 10.30,
    'bigger-plate': 11.80,
}

# Human‑readable names for meal types
MEAL_NAMES = {
    'bowl': 'Bowl',
    'plate': 'Plate',
    'bigger-plate': 'Bigger Plate',
}

MEAL_IMAGES = {
    'bowl': 'kiosk/images/bowl.png',
    'plate': 'kiosk/images/plate.png',
    'bigger-plate': 'kiosk/images/biggerplate.png',
}

ENTREE_REQUIRED = {
    'bowl': 1,
    'plate': 2,
    'bigger-plate': 3,
}

SIDE_REQUIRED = {
    'bowl': 1,
    'plate': 1,
    'bigger-plate': 1,
}

# Define available sides and entrees. These could be stored in the database via
# the ``MenuItem`` model for a more dynamic approach, but for simplicity
# they're kept in plain Python structures here.
SIDES = [
    'Chow Mein',
    'Fried Rice',
    'White Steamed Rice',
    'Super Greens',
]

ENTREES = [
    'Orange Chicken',
    'Beijing Beef',
    'Kung Pao Chicken',
    'Broccoli Beef',
    'Mushroom Chicken',
    'Black Pepper Chicken',
    'String Bean Chicken Breast',
    'SweetFire Chicken Breast',
]

# Pricing for a la carte items by size (S, M, L). Prices are based on
# Panda Express a la carte menu where small portions like Orange Chicken cost
# around $5.40, medium $8.70 and large $11.40【705704416816123†L280-L297】.
# Premium items such as Honey Walnut Shrimp and Black Pepper Sirloin cost
# more at $6.90 (S), $11.70 (M) and $15.90 (L)【705704416816123†L320-L331】.
ALA_CARTE_SIZE_PRICES = {
    'S': 5.40,
    'M': 8.70,
    'L': 11.40,
}

ALA_CARTE_PREMIUM_SIZE_PRICES = {
    'S': 6.90,
    'M': 11.70,
    'L': 15.90,
}

ALA_CARTE_PREMIUM_SIZE_PRICES = {
    'S': 6.90,
    'M': 11.70,
    'L': 15.90,
}


ALA_CARTE_ITEMS = {
    'Orange Chicken': {'S': 5.40, 'M': 8.70, 'L': 11.40},
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

# Pricing for appetizers. Small orders typically cost around $2 while medium
# and large orders scale up; e.g., chicken egg rolls cost $2 for a single
# piece and $11.20 for six pieces【705704416816123†L190-L199】. We approximate
# medium orders at $6.00 and large at $11.20.
APPETIZER_ITEMS = {
    'Chicken Egg Roll': {'S': 2.00, 'M': 6.00, 'L': 11.20},
    'Veggie Spring Roll': {'S': 2.00, 'M': 6.00, 'L': 11.20},
    'Cream Cheese Rangoon': {'S': 2.00, 'M': 6.00, 'L': 8.00},
    'Apple Pie Roll': {'S': 2.00, 'M': 6.20, 'L': 8.00},
    'Chicken Potsticker': {'S': 2.00, 'M': 6.00, 'L': 11.20},
}

# Pricing for drinks. Fountain drinks at Panda Express typically cost $2.20 for
# a small, $2.40 for a medium, and $2.60 for a large【499893808957355†L94-L116】.
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

# Drinks that should present size choices even if the DB only has one price row
FOUNTAIN_DRINKS = {
    'Coca Cola',
    'Diet Coke',
    'Dr Pepper',
    'Sprite',
    'Minute Maid Lemonade',
}

def _with_images(sequence):
    """
    Ensure each item in the sequence has .name and .image attributes for templates.
    Strings are converted to a SimpleNamespace; objects get an image attribute attached.
    """
    mapped = []
    for item in sequence:
        if hasattr(item, "name"):
            item.image = IMAGE_FILENAME_MAP.get(item.name)
            mapped.append(item)
        else:
            name = str(item)
            mapped.append(SimpleNamespace(name=name, image=IMAGE_FILENAME_MAP.get(name)))
    return mapped

def _cached_items_by_type(type_name: str, cache_key: str, ttl: int = 600):
    """Return cached items for a menu type, defaulting to RecipeService lookup."""
    items = cache.get(cache_key)
    if items is None:
        items = list(RecipeService.get_items_by_type(type_name))
        cache.set(cache_key, items, ttl)
    return items


def home(request: HttpRequest) -> HttpResponse:
    """Render the kiosk landing page with meal size options."""
    # Build a list of meal options with slug, display name and price
    meal_options = []
    for slug, price in MEAL_PRICES.items():
        meal_options.append({
            'slug': slug,
            'name': MEAL_NAMES.get(slug, slug.title()),
            'price': price,
            'image': MEAL_IMAGES.get(slug),
        })
    lang = request.session.get('menu_lang', 'en')
    # translate meal option names
    _translate_items_in_list(meal_options, lang, 'name')
    ui = _build_kiosk_ui(lang)
    context = {
        'meal_options': meal_options,
        'kiosk_ui': ui,
        'lang': lang,
    }
    return render(request, 'kiosk/home.html', context)


def choose_side(request: HttpRequest, meal_type: str) -> HttpResponse:
    """Handle side/entree selection for a meal and push it into the cart."""
    meal_type = meal_type.lower()
    if meal_type not in MEAL_PRICES:
        return redirect('customer_kiosk:home')
    required = ENTREE_REQUIRED.get(meal_type, 1)
    side_required = SIDE_REQUIRED.get(meal_type, 1)
    side_hint = f"Choose {side_required} whole side{'s' if side_required > 1 else ''} or {side_required * 2} halves"
    error = ''
    editing_index = request.GET.get('edit')
    cart = request.session.get('cart', [])
    preselected_sides = []
    preselected_entrees = {}
    if editing_index is not None:
        try:
            edit_idx = int(editing_index)
            item = cart[edit_idx]
            if item.get('category') == 'meal' and item.get('meal_type') == meal_type:
                side_entries = item.get('side', [])
                preselected_sides = [entry.get('name') for entry in side_entries]
                for entry in item.get('entrees', []):
                    if isinstance(entry, dict) and entry.get('name'):
                        preselected_entrees[entry['name']] = entry.get('qty', 0)
        except (ValueError, IndexError, TypeError):
            editing_index = None
    sides_qs = _cached_items_by_type('Side', 'kiosk_sides')
    entrees_qs = _cached_items_by_type('Entree', 'kiosk_entrees')
    sides = _with_images(sides_qs if sides_qs else SIDES)
    entrees = _with_images(entrees_qs if entrees_qs else ENTREES)
    for entree in entrees:
        name = getattr(entree, "name", str(entree))
        try:
            entree.pref_qty = int(preselected_entrees.get(name, 0))
        except Exception:
            entree.pref_qty = 0
    if request.method == 'POST':
        selected_sides = request.POST.getlist('sides')
        selected_entrees = {}
        entree_counts = []
        total_entrees = 0
        for idx, entree_obj in enumerate(entrees):
            qty_raw = request.POST.get(f'entree_qty_{idx}')
            try:
                qty = int(qty_raw or 0)
            except ValueError:
                qty = 0
            if qty > 0:
                entree_counts.append({'name': entree_obj.name, 'qty': qty})
                total_entrees += qty
                selected_entrees[entree_obj.name] = qty
        side_names = [s.name for s in sides]
        entree_names = [e.name for e in entrees]
        if len(selected_sides) not in {side_required, side_required * 2}:
            error = f"Select exactly {side_required} side{'s' if side_required > 1 else ''} or {side_required * 2} sides to split into halves."
        elif not all(side in side_names for side in selected_sides):
            error = "Please select valid side(s)."
        elif total_entrees != required:
            error = f"Please select exactly {required} entrée{'s' if required > 1 else ''}."
        elif not all(entry['name'] in entree_names for entry in entree_counts):
            error = "Please select valid entrées."
        else:
            cart = request.session.get('cart', [])
            qty = side_required / len(selected_sides) if selected_sides else 0
            side_entries = [{'name': name, 'qty': qty} for name in selected_sides]
            payload = {
                'category': 'meal',
                'meal_type': meal_type,
                'meal_name': MEAL_NAMES.get(meal_type, meal_type.title()),
                'side': side_entries,
                'entrees': entree_counts,
                'price': MEAL_PRICES.get(meal_type, 0),
            }
            edit_idx = request.POST.get('editing_index')
            if edit_idx is not None:
                try:
                    idx = int(edit_idx)
                    cart[idx] = payload
                except (ValueError, IndexError, TypeError):
                    cart.append(payload)
            else:
                cart.append(payload)
            request.session['cart'] = cart
            request.session.pop('order', None)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'cart_count': len(cart), 'cart_total': _cart_total(request)})
            if edit_idx is not None:
                return redirect('customer_kiosk:cart')
            lang = request.session.get('menu_lang', 'en')
            _translate_items_in_list(sides, lang)
            _translate_items_in_list(entrees, lang)
            ui = _build_kiosk_ui(lang)
            return render(request, 'kiosk/choose_side.html', {
                'meal_type': meal_type,
                'meal_name': translate(MEAL_NAMES.get(meal_type, meal_type.title()), lang),
                'sides': sides,
                'entrees': entrees,
                'required': required,
                'side_required': side_required,
                'side_hint': translate(side_hint, lang),
                'error': '',
                'added': True,
                'hide_cart_button': True,
                'cart_total': _cart_total(request),
                'kiosk_ui': ui,
                'lang': lang,
            })
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and error:
            return JsonResponse({'status': 'error', 'message': error, 'cart_total': _cart_total(request)}, status=400)
    lang = request.session.get('menu_lang', 'en')
    _translate_items_in_list(sides, lang)
    _translate_items_in_list(entrees, lang)
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/choose_side.html', {
        'meal_type': meal_type,
        'meal_name': translate(MEAL_NAMES.get(meal_type, meal_type.title()), lang),
        'sides': sides,
        'entrees': entrees,
        'required': required,
        'side_required': side_required,
        'error': translate(error, lang) if error else '',
        'hide_cart_button': True,
        'editing_index': editing_index,
        'is_editing': editing_index is not None,
        'preselected_sides': preselected_sides,
        'preselected_entrees': preselected_entrees,
        'side_hint': translate(f"Choose {side_required} whole side{'' if side_required == 1 else 's'} or {side_required * 2} halves", lang),
        'cart_total': _cart_total(request),
        'kiosk_ui': ui,
        'lang': lang,
    })


def choose_entrees(request: HttpRequest, meal_type: str) -> HttpResponse:
    """Collect entrée quantities for an in-progress meal selection."""
    meal_type = meal_type.lower()
    if meal_type not in MEAL_PRICES:
        return redirect('customer_kiosk:home')
    required = ENTREE_REQUIRED.get(meal_type, 1)
    error = ''
    entrees_qs = _cached_items_by_type('Entree', 'kiosk_entrees')
    entrees = _with_images(entrees_qs if entrees_qs else ENTREES)
    editing_index = request.GET.get('edit')
    cart = request.session.get('cart', [])
    selected_entrees = {}
    if editing_index is not None:
        try:
            edit_idx = int(editing_index)
            item = cart[edit_idx]
            if item.get('category') == 'meal' and item.get('meal_type') == meal_type:
                for entry in item.get('entrees', []):
                    selected_entrees[entry['name']] = entry.get('qty', 0)
        except (ValueError, IndexError, TypeError):
            editing_index = None

    def _parse_entree_counts() -> tuple[list[dict], int]:
        counts = []
        total = 0
        for idx, entree in enumerate(entrees):
            qty_raw = request.POST.get(f'entree_qty_{idx}')
            try:
                qty = int(qty_raw or 0)
            except ValueError:
                qty = 0
            if qty > 0:
                counts.append({'name': entree.name, 'qty': qty})
                total += qty
        return counts, total

    if request.method == 'POST':
        counts, total = _parse_entree_counts()
        if total != required:
            # Build the same message but translate to the user's language
            lang = request.session.get('menu_lang', 'en')
            raw_err = f"Please select exactly {required} entrée{'s' if required > 1 else ''}."
            error = translate(raw_err, lang)
        else:
            order = request.session.get('order', {})
            order['entrees'] = counts
            meal_type_slug = order.get('meal_type')
            side = order.get('side')
            if meal_type_slug and side:
                item = {
                    'category': 'meal',
                    'meal_type': meal_type_slug,
                    'meal_name': MEAL_NAMES.get(meal_type_slug, meal_type_slug.title()),
                    'side': side,
                    'entrees': counts,
                    'price': MEAL_PRICES.get(meal_type_slug, 0),
                }
                cart = request.session.get('cart', [])
                cart.append(item)
                request.session['cart'] = cart
            if 'order' in request.session:
                del request.session['order']
            return redirect('customer_kiosk:cart')
    lang = request.session.get('menu_lang', 'en')
    _translate_items_in_list(entrees, lang)
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/choose_entrees.html', {
        'meal_type': meal_type,
        'meal_name': translate(MEAL_NAMES.get(meal_type, meal_type.title()), lang),
        'entrees': entrees,
        'required': required,
        'error': translate(error, lang) if error else '',
        'is_editing': editing_index is not None,
        'selected_entrees': selected_entrees,
        'kiosk_ui': ui,
        'lang': lang,
    })


def review_order(request: HttpRequest) -> HttpResponse:
    order = request.session.get('order')
    if not order:
        return redirect('customer_kiosk:home')
    meal_type = order.get('meal_type')
    side = order.get('side')
    entrees = order.get('entrees', [])
    base_price = MEAL_PRICES.get(meal_type, 0)
    total = base_price
    lang = request.session.get('menu_lang', 'en')
    # Translate side and entree names for display
    if isinstance(side, list):
        for s in side:
            if isinstance(s, dict) and s.get('name'):
                s['translated_name'] = translate(s['name'], lang)
    for e in entrees:
        if isinstance(e, dict) and e.get('name'):
            e['translated_name'] = translate(e['name'], lang)
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/review.html', {
        'meal_type': meal_type,
        'meal_name': translate(MEAL_NAMES.get(meal_type, meal_type.title()) if meal_type else '', lang) if meal_type else None,
        'side': side,
        'entrees': entrees,
        'base_price': base_price,
        'total': total,
        'kiosk_ui': ui,
        'lang': lang,
    })


def choose_a_la_carte(request: HttpRequest) -> HttpResponse:
    """A la carte item selection with translation support."""
    lang = request.session.get("menu_lang", "en")

    # Fetch entrée items
    items_qs = _cached_items_by_type('Entree', 'kiosk_entrees')
    items = [{
        'name': i.name,
        'price': float(i.price) if isinstance(i.price, (Decimal, float, int)) else 0,
        'prices': {'S': float(i.price), 'M': float(i.price), 'L': float(i.price)} if isinstance(i.price, (Decimal, float, int)) else {},
        'image': IMAGE_FILENAME_MAP.get(i.name),
    } for i in items_qs]

    # If DB empty, fall back to ALA_CARTE_ITEMS
    if not items:
        items = [{
            'name': name,
            'price': price_dict.get('M', list(price_dict.values())[0]),
            'prices': price_dict,
            'image': IMAGE_FILENAME_MAP.get(name),
        } for name, price_dict in sorted(ALA_CARTE_ITEMS.items())]

    # ======== TRANSLATE ITEM NAMES (batch) ========
    item_names = [i["name"] for i in items]
    translated_map = translate_many(item_names, lang)

    for i in items:
        i["translated_name"] = translated_map.get(i["name"], i["name"])

    # ======== Translate size labels ========
    base_labels = {"S": "Small", "M": "Medium", "L": "Large"}
    translated_labels = translate_many(base_labels.values(), lang)
    translated_size_labels = {
        size: translated_labels[base_labels[size]]
        for size in base_labels
    }

    size_prices = [{
        'code': size,
        'label': translated_size_labels[size],
        'price': ALA_CARTE_SIZE_PRICES.get(size, 0),
    } for size in ('S','M','L')]

    # Editing support
    editing_index = request.GET.get('edit')
    selected_item, selected_size = None, None
    cart = request.session.get('cart', [])

    if editing_index is not None:
        try:
            idx = int(editing_index)
            existing = cart[idx]
            if existing.get('category') == 'a_la_carte':
                selected_item = existing.get('name')
                selected_size = existing.get('size')
            else:
                editing_index = None
        except Exception:
            editing_index = None

    added = bool(request.session.pop('kiosk_alacarte_added', False))
    error = ''

    # ======== POST HANDLING ========
    if request.method == 'POST':
        item_name = request.POST.get('item')
        size = request.POST.get('size')
        match = next((i for i in items if i['name'] == item_name), None)

        if match and size in ('S', 'M', 'L'):
            # Determine premium price
            price = ALA_CARTE_SIZE_PRICES[size]
            base_price = float(match.get('price') or 0)
            if base_price > 0:
                price = ALA_CARTE_PREMIUM_SIZE_PRICES.get(size, price)

            payload = {
                'category': 'a_la_carte',
                'name': item_name,
                'size': size,
                'price': price,
            }

            edit_idx = request.POST.get('editing_index')
            if edit_idx is not None:
                try:
                    idx = int(edit_idx)
                    cart[idx] = payload
                except:
                    cart.append(payload)
                request.session['cart'] = cart
                return redirect('customer_kiosk:cart')

            cart.append(payload)
            request.session['cart'] = cart
            request.session['kiosk_alacarte_added'] = True
            return redirect('customer_kiosk:a_la_carte')

        error = translate("Please select an item and size.", lang)

    # Premium items (for JS frontend)
    premium_items = [item['name'] for item in items if float(item.get('price') or 0) != 0]
    premium_size_prices = [
        {'code': size, 'price': ALA_CARTE_PREMIUM_SIZE_PRICES.get(size, 0)}
        for size in ('S','M','L')
    ]

    context = {
        'items': items,
        'sizes': size_prices,
        'error': error,
        'added': added,
        'hide_cart_button': True,
        'alacarte_payload': {
            'sizes': size_prices,
            'premiumItems': premium_items,
            'premiumSizePrices': premium_size_prices,
        },
        'is_editing': editing_index is not None,
        'editing_index': editing_index,
        'selected_item': selected_item,
        'selected_size': selected_size,
        'cart_total': _cart_total(request),
        'lang': lang,
        'kiosk_ui': _build_kiosk_ui(lang),
    }

    return render(request, 'kiosk/choose_a_la_carte.html', context)



def choose_appetizer(request: HttpRequest) -> HttpResponse:
    """Allow the user to select an appetizer item and size."""
    items_qs = _cached_items_by_type('Appetizer', 'kiosk_appetizers')
    items = [{
        'name': i.name,
        'price': APPETIZER_ITEMS.get(i.name, {}).get('M', float(i.price) if isinstance(i.price, (Decimal, float, int)) else 0),
        'prices': APPETIZER_ITEMS.get(i.name, {'S': float(i.price), 'M': float(i.price), 'L': float(i.price)}) if isinstance(i.price, (Decimal, float, int)) else APPETIZER_ITEMS.get(i.name, {}),
        'image': IMAGE_FILENAME_MAP.get(i.name),
    } for i in items_qs]
    if not items:
        items = [{
            'name': name,
            'price': price_dict.get('M', list(price_dict.values())[0]),
            'prices': price_dict,
            'image': IMAGE_FILENAME_MAP.get(name),
        } for name, price_dict in sorted(APPETIZER_ITEMS.items())]
    editing_index = request.GET.get('edit')
    selected_item = None
    selected_size = None
    cart = request.session.get('cart', [])
    if editing_index is not None:
        try:
            idx = int(editing_index)
            existing = cart[idx]
            if existing.get('category') == 'appetizer':
                selected_item = existing.get('name')
                selected_size = existing.get('size')
            else:
                editing_index = None
        except (ValueError, IndexError, TypeError):
            editing_index = None
    added = bool(request.session.pop('kiosk_app_added', False))
    error = ''
    if request.method == 'POST':
        item_name = request.POST.get('item')
        size = request.POST.get('size')
        match = next((i for i in items if i['name'] == item_name), None)
        if match and size in ('S', 'M', 'L'):
            price = match['prices'].get(size, match['price'])
            payload = {
                'category': 'appetizer',
                'name': item_name,
                'size': size,
                'price': price,
            }
            edit_idx = request.POST.get('editing_index')
            if edit_idx is not None:
                try:
                    idx = int(edit_idx)
                    if 0 <= idx < len(cart):
                        cart[idx] = payload
                    else:
                        cart.append(payload)
                except (ValueError, IndexError, TypeError):
                    cart.append(payload)
                request.session['cart'] = cart
                return redirect('customer_kiosk:cart')
            cart.append(payload)
            request.session['cart'] = cart
            added = True
        else:
            lang = request.session.get('menu_lang', 'en')
            error = translate("Please select an item and size.", lang)
    lang = request.session.get('menu_lang', 'en')
    _translate_items_in_list(items, lang)
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/choose_appetizer.html', {
        'items': items,
        'error': error,
        'added': added,
        'hide_cart_button': True,
        'is_editing': editing_index is not None,
        'editing_index': editing_index,
        'selected_item': selected_item,
        'selected_size': selected_size,
        'price_map': {item['name']: item['prices'] for item in items},
        'cart_total': _cart_total(request),
        'kiosk_ui': ui,
        'lang': lang,
    })


def choose_drink(request: HttpRequest) -> HttpResponse:
    """Allow the user to select a drink and size."""
    items_qs = _cached_items_by_type('Drink', 'kiosk_drinks')
    items = []
    for drink in items_qs:
        base_price = float(drink.price) if isinstance(drink.price, (Decimal, float, int)) else 0
        mapped = DRINK_ITEMS.get(drink.name)
        if mapped:
            prices = mapped
            has_sizes = len(mapped) > 1
        elif drink.name in FOUNTAIN_DRINKS:
            prices = {'S': base_price, 'M': base_price, 'L': base_price}
            has_sizes = True
        else:
            prices = {'M': base_price}
            has_sizes = False
        items.append({
            'name': drink.name,
            'price': prices.get('M', base_price),
            'prices': prices,
            'image': IMAGE_FILENAME_MAP.get(drink.name),
            'has_sizes': has_sizes,
        })
    if not items:
        items = [{
            'name': name,
            'prices': price_dict,
            'image': IMAGE_FILENAME_MAP.get(name),
            'has_sizes': len(price_dict) > 1,
            'price': price_dict.get('M', list(price_dict.values())[0]),
        } for name, price_dict in sorted(DRINK_ITEMS.items())]
    editing_index = request.GET.get('edit')
    selected_item = None
    selected_size = None
    cart = request.session.get('cart', [])
    if editing_index is not None:
        try:
            idx = int(editing_index)
            existing = cart[idx]
            if existing.get('category') == 'drink':
                selected_item = existing.get('name')
                selected_size = existing.get('size')
            else:
                editing_index = None
        except (ValueError, IndexError, TypeError):
            editing_index = None
    added = bool(request.session.pop('kiosk_drink_added', False))
    error = ''
    if request.method == 'POST':
        item_name = request.POST.get('item')
        size = request.POST.get('size')
        match = next((i for i in items if i['name'] == item_name), None)
        if match and size in ('S', 'M', 'L'):
            price = match['prices'].get(size, match['price'])
            payload = {
                'category': 'drink',
                'name': item_name,
                'size': size,
                'price': price,
            }
            edit_idx = request.POST.get('editing_index')
            if edit_idx is not None:
                try:
                    idx = int(edit_idx)
                    if 0 <= idx < len(cart):
                        cart[idx] = payload
                    else:
                        cart.append(payload)
                except (ValueError, IndexError, TypeError):
                    cart.append(payload)
                request.session['cart'] = cart
                return redirect('customer_kiosk:cart')
            cart.append(payload)
            request.session['cart'] = cart
            request.session['kiosk_drink_added'] = True
            request.session.modified = True
            return redirect('customer_kiosk:drinks')
        else:
            lang = request.session.get('menu_lang', 'en')
            error = translate("Please select an item and size.", lang)
    lang = request.session.get('menu_lang', 'en')
    _translate_items_in_list(items, lang)
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/choose_drink.html', {
        'items': items,
        'error': error,
        'added': added,
        'hide_cart_button': True,
        'is_editing': editing_index is not None,
        'editing_index': editing_index,
        'selected_item': selected_item,
        'selected_size': selected_size,
        'price_map': {item['name']: item['prices'] for item in items},
        'has_sizes_map': {item['name']: bool(item.get('has_sizes')) and len(item.get('prices', {})) > 1 for item in items},
        'single_price_map': {item['name']: item.get('price') for item in items},
        'cart_total': _cart_total(request),
        'kiosk_ui': ui,
        'lang': lang,
    })

def add_to_cart_api(request: HttpRequest) -> JsonResponse:
    """Lightweight endpoint to add items to cart without a full page reload (drinks/appetizers/a_la_carte)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    payload = {}
    try:
        import json
        if request.body:
            payload = json.loads(request.body.decode() or "{}")
    except Exception:
        payload = {}
    # Merge POST form data over JSON payload
    for key, value in request.POST.items():
        payload[key] = value

    category = payload.get('category')
    if category == 'drink':
        item_name = payload.get('item')
        size = payload.get('size')
        if not item_name or size not in ('S', 'M', 'L'):
            return JsonResponse({'status': 'error', 'message': 'Invalid item or size'}, status=400)

        # Build drink price map (same as choose_drink)
        items_qs = _cached_items_by_type('Drink', 'kiosk_drinks')
        items = []
        for drink in items_qs:
            base_price = float(drink.price) if isinstance(drink.price, (Decimal, float, int)) else 0
            mapped = DRINK_ITEMS.get(drink.name)
            if mapped:
                prices = mapped
            elif drink.name in FOUNTAIN_DRINKS:
                prices = {'S': base_price, 'M': base_price, 'L': base_price}
            else:
                prices = {'M': base_price}
            items.append({
                'name': drink.name,
                'price': prices.get('M', base_price),
                'prices': prices,
            })
        if not items:
            items = [{
                'name': name,
                'prices': price_dict,
                'price': price_dict.get('M', list(price_dict.values())[0]),
            } for name, price_dict in sorted(DRINK_ITEMS.items())]
        match = next((i for i in items if i['name'] == item_name), None)
        if not match:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=400)
        price = match['prices'].get(size, match['price'])
        cart_item = {
            'category': 'drink',
            'name': item_name,
            'size': size,
            'price': price,
        }
    elif category == 'appetizer':
        item_name = payload.get('item')
        size = payload.get('size')
        if not item_name or size not in ('S', 'M', 'L'):
            return JsonResponse({'status': 'error', 'message': 'Invalid item or size'}, status=400)
        items_qs = _cached_items_by_type('Appetizer', 'kiosk_appetizers')
        items = [{
            'name': i.name,
            'price': APPETIZER_ITEMS.get(i.name, {}).get('M', float(i.price) if isinstance(i.price, (Decimal, float, int)) else 0),
            'prices': APPETIZER_ITEMS.get(i.name, {'S': float(i.price), 'M': float(i.price), 'L': float(i.price)}) if isinstance(i.price, (Decimal, float, int)) else APPETIZER_ITEMS.get(i.name, {}),
        } for i in items_qs]
        if not items:
            items = [{
                'name': name,
                'price': price_dict.get('M', list(price_dict.values())[0]),
                'prices': price_dict,
            } for name, price_dict in sorted(APPETIZER_ITEMS.items())]
        match = next((i for i in items if i['name'] == item_name), None)
        if not match:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=400)
        price = match['prices'].get(size, match['price'])
        cart_item = {
            'category': 'appetizer',
            'name': item_name,
            'size': size,
            'price': price,
        }
    elif category == 'a_la_carte':
        item_name = payload.get('item')
        size = payload.get('size')
        if not item_name or size not in ('S', 'M', 'L'):
            return JsonResponse({'status': 'error', 'message': 'Invalid item or size'}, status=400)
        items_qs = _cached_items_by_type('Entree', 'kiosk_entrees')
        items = [{
            'name': i.name,
            'price': float(i.price) if isinstance(i.price, (Decimal, float, int)) else 0,
            'prices': {'S': float(i.price), 'M': float(i.price), 'L': float(i.price)} if isinstance(i.price, (Decimal, float, int)) else {},
        } for i in items_qs]
        if not items:
            items = [{
                'name': name,
                'price': price_dict.get('M', list(price_dict.values())[0]),
                'prices': price_dict,
            } for name, price_dict in sorted(ALA_CARTE_ITEMS.items())]
        premium_items = [item['name'] for item in items if float(item.get('price') or 0) != 0]
        price_lookup = {size_code: ALA_CARTE_SIZE_PRICES.get(size_code, 0) for size_code in ('S', 'M', 'L')}
        premium_lookup = {size_code: ALA_CARTE_PREMIUM_SIZE_PRICES.get(size_code, 0) for size_code in ('S', 'M', 'L')}
        match = next((i for i in items if i['name'] == item_name), None)
        if not match:
            return JsonResponse({'status': 'error', 'message': 'Item not found'}, status=400)
        base_price = float(match.get('price') or 0)
        price = premium_lookup[size] if match['name'] in premium_items else price_lookup.get(size, base_price)
        cart_item = {
            'category': 'a_la_carte',
            'name': item_name,
            'size': size,
            'price': price,
        }
    else:
        return JsonResponse({'status': 'error', 'message': 'Unsupported category'}, status=400)

    cart = request.session.get('cart', [])
    cart.append(cart_item)
    request.session['cart'] = cart
    request.session.modified = True
    return JsonResponse({'status': 'ok', 'cart_count': len(cart), 'cart_total': _cart_total(request)})

def cart_summary(request: HttpRequest) -> HttpResponse:
    """Display all items currently in the cart and the total cost."""
    cart = request.session.get('cart', [])
    recipe_map = _resolve_recipe_mapping(cart)
    total = _refresh_cart_prices(cart, recipe_map)
    request.session['cart'] = cart

    lang = request.session.get('menu_lang', 'en')
    def _format_entry(entry):
        if isinstance(entry, dict):
            raw_name = entry.get('name') or ""
            name = translate(raw_name, lang) if raw_name else raw_name
            qty = entry.get('qty', 1)
            if qty < 1:
                return f"{name} (½)"
            elif qty > 1:
                return f"{name} × {qty}"
            return name
        return str(entry)

    cart_with_display = []
    for item in cart:
        side = item.get('side')
        if isinstance(side, (list, tuple)):
            sides = [_format_entry(s) for s in side if s]
            side_display = ", ".join(sides) if sides else "-"
        elif side:
            side_display = _format_entry(side)
        else:
            side_display = "-"

        entree_display = "-"
        entrees = item.get('entrees')
        if isinstance(entrees, (list, tuple)):
            entries = [_format_entry(e) for e in entrees if e]
            entree_display = ", ".join(entries) if entries else "-"
        elif entrees:
            entree_display = _format_entry(entrees)

        if item.get('category') == 'meal':
            connector = translate(' with ', lang).strip() or ' with '
            selection_text = side_display
            if entree_display and entree_display != "-":
                selection_text = f"{side_display}{connector if side_display and side_display != '-' else ''}{entree_display}"
        else:
            selection_text = item.get('name') or item.get('category') or "-"

        cart_with_display.append({**item,
            'side_display': side_display,
            'entree_display': entree_display,
            'selection_text': selection_text})
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/cart.html', {
        'cart': cart_with_display,
        'total': total,
        'hide_cart_button': True,
        'content_class': 'kiosk-content-inner--no-scroll',
        'kiosk_ui': ui,
        'lang': lang,
    })


def remove_from_cart(request: HttpRequest, index: int) -> HttpResponse:
    """Remove a single item from the cart by index."""
    cart = request.session.get('cart', [])
    if 0 <= index < len(cart):
        del cart[index]
        request.session['cart'] = cart
    return redirect('customer_kiosk:cart')

def _sanitize_name(name: str) -> str:
    """Remove price suffixes and excess whitespace from a recipe name."""
    if not name:
        return ""
    return re.sub(r'\s*\(\$[^)]*\)\s*$', '', name).strip()

def _normalize_name(name: str) -> str:
    """Lowercase, sanitized recipe names for consistent lookups."""
    cleaned = _sanitize_name(name)
    return cleaned.lower() if cleaned else ""


def _extract_recipe_names(item: dict) -> list[str]:
    """Return every recipe name referenced by a cart item."""
    names = []
    if item.get('category') == 'meal':
        sides = item.get('side', [])
        if isinstance(sides, (list, tuple)):
            for side in sides:
                if isinstance(side, dict):
                    if side.get('name'):
                        names.append(side['name'])
                elif side:
                    names.append(side)
        elif sides:
            names.append(sides)
        entrees = item.get('entrees', [])
        if isinstance(entrees, (list, tuple)):
            for entree in entrees:
                qty = 0
                name = ""
                if isinstance(entree, dict):
                    name = entree.get('name')
                    qty = int(entree.get('qty') or 0)
                else:
                    name = entree
                    qty = 1
                if name:
                    if qty > 1:
                        names.extend([name] * qty)
                    else:
                        names.append(name)
        elif entrees:
            names.append(entrees)
    else:
        name = item.get('name')
        if name:
            names.append(name)
    return [str(n) for n in names if n]


def _resolve_recipe_mapping(cart: list[dict]) -> dict[str, Recipe]:
    """Map normalized names from the cart to Recipe instances that exist in the database."""
    mapping: dict[str, Recipe] = {}
    for item in cart:
        for name in _extract_recipe_names(item):
            lookup = _sanitize_name(name)
            if not lookup:
                continue
            key = lookup.lower()
            if key in mapping:
                continue
            recipe = Recipe.objects.filter(name__iexact=lookup, active=True).first()
            if recipe:
                mapping[key] = recipe
    return mapping


def _refresh_cart_prices(cart: list[dict], recipe_map: dict[str, Recipe]) -> float:
    """Override cart prices with database values when available and return the recalculated total."""
    total = 0.0
    for item in cart:
        if item.get('category') == 'meal':
            base_price = float(MEAL_PRICES.get(item.get('meal_type')) or 0)
            extras = 0.0
            for name in _extract_recipe_names(item):
                normalized = _normalize_name(name)
                recipe = recipe_map.get(normalized)
                if recipe:
                    extras += float(recipe.price)
            price = base_price + extras
            item['price'] = price
        else:
            price = float(item.get('price') or 0)
            normalized = _normalize_name(item.get('name'))
            recipe = recipe_map.get(normalized)
            # Preserve explicit prices for a la carte entries (they depend on size)
            if recipe and item.get('category') not in ('a_la_carte', 'drink', 'appetizer'):
                recipe_price = float(recipe.price)
                if recipe_price > 0:
                    price = recipe_price
                    item['price'] = price
        total += price
    return total


def _cart_total(request: HttpRequest) -> float:
    """Return the current cart total while keeping session pricing in sync."""
    cart = request.session.get('cart', [])
    recipe_map = _resolve_recipe_mapping(cart)
    total = _refresh_cart_prices(cart, recipe_map)
    request.session['cart'] = cart
    request.session.modified = True
    return total


def _collect_recipe_ids(cart: list[dict], recipe_map: dict[str, Recipe]) -> list[int]:
    """List every recipe id that should be associated with the order."""
    recipe_ids: list[int] = []
    for item in cart:
        for name in _extract_recipe_names(item):
            normalized = _normalize_name(name)
            recipe = recipe_map.get(normalized)
            if recipe:
                recipe_ids.append(recipe.id)
    return recipe_ids


def order_confirmation(request: HttpRequest) -> HttpResponse:
    """Display a confirmation page after the order is placed and notify kitchen via websocket."""
    from django.contrib.auth import logout
    
    cart = request.session.get('cart', [])
    last_order_id = request.session.get('last_order_id')
    if not last_order_id:
        # Preserve the order id through the OAuth login redirect even if the session was rotated/cleared.
        order_id_param = request.GET.get('order_id')
        try:
            last_order_id = int(order_id_param)
        except (TypeError, ValueError):
            last_order_id = None
    
    # Check if user just logged in and wants email receipt
    if request.user.is_authenticated and last_order_id:
        # Check if we should send email (user just came back from OAuth)
        send_email_flag = request.session.pop('send_receipt_email', False)
        if send_email_flag:
            user_email = request.user.email
            if user_email:
                if _send_receipt_email(request, last_order_id, user_email):
                    email_sent_info = {
                        'order_id': last_order_id,
                        'email': user_email,
                        'status': 'ok',
                    }
                else:
                    email_sent_info = {
                        'order_id': last_order_id,
                        'email': user_email,
                        'status': 'error',
                    }
            else:
                email_sent_info = {
                    'order_id': last_order_id,
                    'email': None,
                    'status': 'missing',
                }
            # Persist email_sent_info and essential order metadata across logout
            order_carts_snapshot = request.session.get('order_carts')
            session_after_logout = {
                'email_sent_info': email_sent_info,
                'last_order_id': last_order_id,
            }
            if order_carts_snapshot:
                session_after_logout['order_carts'] = order_carts_snapshot
            # Logout user after sending email to ensure fresh login next time
            logout(request)
            for key, value in session_after_logout.items():
                request.session[key] = value
            request.session.modified = True
            return redirect('customer_kiosk:email_sent')
            
    
    if not cart and last_order_id:
        # Allow revisiting confirmation (e.g., after auth flow) using the last order id.
        order = Order.objects.filter(id=last_order_id).first()
        lang = request.session.get('menu_lang', 'en')
        ui = _build_kiosk_ui(lang)
        return render(request, 'kiosk/order_confirmation.html', {
            'cart': [],
            'total': getattr(order, 'price', 0),
            'hide_cart_button': True,
            'content_class': 'kiosk-content-inner--no-scroll',
            'order_id': last_order_id,
            'kiosk_ui': ui,
            'lang': lang,
        })
    if not cart:
        return redirect('customer_kiosk:home')

    recipe_map = _resolve_recipe_mapping(cart)
    total = _refresh_cart_prices(cart, recipe_map)

    order = Order.objects.create(
        price=total,
        time=timezone.now(),
        employee=None,
    )
    recipe_ids = _collect_recipe_ids(cart, recipe_map)
    if recipe_ids:
        with connection.cursor() as cursor:
            for recipe_id in recipe_ids:
                cursor.execute(
                    "INSERT INTO recipe_orders (recipe_id, order_id) VALUES (%s, %s)",
                    [recipe_id, order.id],
                )

    try:
        Utils.DecreaseInventoryForOrder(order)
    except Exception:
        pass

    channel_layer = get_channel_layer()
    if channel_layer is not None:
        try:
            async_to_sync(channel_layer.group_send)(
                "orders",
                {
                    "type": "order.update",
                    "message": {
                        "order_id": order.id,
                        "items": cart,
                        "total": total,
                    },
                },
            )
        except Exception:
            pass

    low_stock_items = []
    recipe_instances = list({recipe.id: recipe for recipe in recipe_map.values()}.values())
    if recipe_instances:
        ingredient_qs = Inventory.objects.filter(recipes__in=recipe_instances).distinct()
        low_qs = ingredient_qs.filter(quantity__lte=F("minimum_stock")).values_list("ingredient", flat=True)
        low_stock_items = list(low_qs)
        if low_stock_items and channel_layer is not None:
            try:
                async_to_sync(channel_layer.group_send)(
                    "orders",
                    {
                        "type": "inventory.update",
                        "message": {"low_stock_items": low_stock_items},
                    },
                )
            except Exception:
                pass

    # Save cart data for receipt generation
    if 'order_carts' not in request.session:
        request.session['order_carts'] = {}
    request.session['order_carts'][str(order.id)] = {
        'cart': cart,
        'total': total,
    }
    request.session.modified = True
    
    request.session['cart'] = []
    request.session['last_order_id'] = order.id

    lang = request.session.get('menu_lang', 'en')
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/order_confirmation.html', {
        'cart': cart,
        'total': total,
        'hide_cart_button': True,
        'content_class': 'kiosk-content-inner--no-scroll',
        'order_id': order.id,
        'kiosk_ui': ui,
        'lang': lang,
    })


def _get_receipt_context(request: HttpRequest, order_id: int) -> dict:
    """Helper function to generate receipt context data for both print and email."""
    order = Order.objects.filter(id=order_id).first()
    if not order:
        return None
    
    # Try to get saved cart data from session
    order_carts = request.session.get('order_carts', {})
    order_data = order_carts.get(str(order_id))
    
    receipt_items = []
    subtotal = 0.0
    
    if order_data and 'cart' in order_data:
        # Use saved cart data with actual prices
        cart = order_data['cart']
        
        def _format_entry(entry):
            if isinstance(entry, dict):
                name = entry.get('name') or ""
                qty = entry.get('qty', 1)
                if qty < 1:
                    return f"{name} (½)"
                elif qty > 1:
                    return f"{name} × {qty}"
                return name
            return str(entry)
        
        for item in cart:
            item_name = ""
            item_price = float(item.get('price', 0))
            
            if item.get('category') == 'meal':
                # Format meal items
                meal_name = item.get('meal_name', '')
                sides = item.get('side', [])
                entrees = item.get('entrees', [])
                
                side_parts = []
                if isinstance(sides, (list, tuple)):
                    side_parts = [_format_entry(s) for s in sides if s]
                elif sides:
                    side_parts = [_format_entry(sides)]
                
                entree_parts = []
                if isinstance(entrees, (list, tuple)):
                    entree_parts = [_format_entry(e) for e in entrees if e]
                elif entrees:
                    entree_parts = [_format_entry(entrees)]
                
                item_name = meal_name
                if side_parts:
                    item_name += " - " + ", ".join(side_parts)
                if entree_parts:
                    item_name += " with " + ", ".join(entree_parts)
            else:
                # A la carte, appetizer, drink
                name = item.get('name', '')
                size = item.get('size', '')
                if size:
                    item_name = f"{name} ({size})"
                else:
                    item_name = name
            
            receipt_items.append({
                'name': item_name,
                'price': item_price,
            })
            subtotal += item_price
    else:
        # Fallback: use recipe data from database
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT r.name, r.price, ro.recipe_id
                FROM recipe_orders ro
                JOIN recipes r ON ro.recipe_id = r.id
                WHERE ro.order_id = %s
                ORDER BY r.name
                """,
                [order_id]
            )
            recipe_rows = cursor.fetchall()
        
        for name, price, recipe_id in recipe_rows:
            receipt_items.append({
                'name': name,
                'price': float(price) if price else 0.0,
            })
        
        subtotal = float(order.price) if order.price else 0.0
    
    tax = subtotal * 0.0825  # Texas sales tax
    total = subtotal + tax
    
    # Generate a random fortune message for the receipt
    try:
        from core.utils import Utils
        fortune_message = Utils.generate_fortune()
    except Exception:
        fortune_message = ""

    # Translate receipt item names for the kiosk language
    lang = request.session.get('menu_lang', 'en')
    for it in receipt_items:
        name = it.get('name')
        it['translated_name'] = translate(name, lang) if name else name

    context = {
        'order': order,
        'order_id': order_id,
        'items': receipt_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'order_time': order.time,
        'fortune': fortune_message,
        'kiosk_ui': _build_kiosk_ui(lang),
        'lang': lang,
    }
    return context


def _send_receipt_email(request: HttpRequest, order_id: int, user_email: str) -> bool:
    """Send receipt email to the user using Azure Communication Services. Returns True if successful."""
    try:
        context = _get_receipt_context(request, order_id)
        if not context:
            return False
        
        # Add email-specific flag to hide print button
        context['is_email'] = True
        
        # Render HTML email
        html_content = render_to_string('kiosk/receipt.html', context)
        
        # Initialize Azure Email Service
        azure_email_service = AzureEmailService()
        
        # Send email using Azure Communication Services
        success = azure_email_service.send_receipt_email(
            recipient_email=user_email,
            order_id=order_id,
            html_content=html_content,
            total_amount=context.get("total", 0.0)
        )
        
        return success
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def print_receipt(request: HttpRequest, order_id: int) -> HttpResponse:
    """Generate and display a printable HTML receipt for an order."""
    context = _get_receipt_context(request, order_id)
    if not context:
        return redirect('customer_kiosk:home')
    
    return render(request, 'kiosk/receipt.html', context)


def email_sent(request: HttpRequest) -> HttpResponse:
    """
    Landing page after sending a receipt email (post login/signup).
    Always clear prior messages and avoid leaking any previous user context.
    """
    info = request.session.pop('email_sent_info', {}) or {}
    order_id = info.get('order_id') or request.session.get('last_order_id')
    email = info.get('email')
    status = info.get('status')

    # Hide lingering messages
    from django.contrib import messages
    storage = messages.get_messages(request)
    list(storage)  # exhaust

    if not order_id:
        return redirect('customer_kiosk:home')

    lang = request.session.get('menu_lang', 'en')
    ui = _build_kiosk_ui(lang)
    return render(request, 'kiosk/email_sent.html', {
        'order_id': order_id,
        'email': email,
        'status': status,
        'order_url': f"{request.build_absolute_uri('/kiosk/order-confirmation/')}?order_id={order_id}",
        'hide_cart_button': True,
        'content_class': 'kiosk-content-inner--no-scroll',
        'kiosk_ui': ui,
        'lang': lang,
    })

def set_email_flag(request: HttpRequest) -> HttpResponse:
    """Set session flag to send email receipt after OAuth login."""
    if request.method == 'POST':
        # Preserve order/session data, then flush to drop auth + old messages so no prior email is reused.
        last_order_id = request.session.get('last_order_id')
        order_carts = request.session.get('order_carts')
        cart = request.session.get('cart')
        try:
            import json
            payload = json.loads(request.body or "{}")
        except Exception:
            payload = {}
        receipt_return_to = payload.get("next")

        # Flush resets the session (auth + messages) to avoid leaking the previous account.
        request.session.flush()

        # Restore only what the confirmation page needs.
        if last_order_id:
            request.session['last_order_id'] = last_order_id
        if order_carts:
            request.session['order_carts'] = order_carts
        if cart:
            request.session['cart'] = cart
        if receipt_return_to:
            request.session['receipt_return_to'] = receipt_return_to
        # Clear any prior email-sent info/messages.
        request.session.pop('email_sent_info', None)

        request.session['send_receipt_email'] = True
        request.session.modified = True
        return HttpResponse(status=200)
    return HttpResponse(status=400)

def kiosk_translations(lang: str):
    # UI strings shown in the base kiosk template
    strings = {
        "brand_panda": "Panda",
        "brand_express": "Express",
        "menu_categories": "Menu Categories",

        "nav_bowl": "Bowl",
        "nav_plate": "Plate",
        "nav_bigger_plate": "Bigger Plate",
        "nav_a_la_carte": "A La Carte",
        "nav_appetizers": "Appetizers",
        "nav_drinks": "Drinks",
        "nav_cart": "Cart",

        "view_cart": "View Cart",

        "change_language": "Change language",
        "choose_language": "Choose Language",
    }

    # Translate everything in bulk
    translated = translate_many(strings.values(), lang)

    # Re-map into the same keys
    return {key: translated[value] for key, value in strings.items()}