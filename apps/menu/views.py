"""
Module apps.kitchen.views

This module contains view functions for the Kitchen app, including:
- Menu display with translation support
- Cycling menu languages
- Fetching and displaying current weather

It relies on:
- Django ORM (Recipe model)
- Custom translation and weather helper functions


"""

from django.shortcuts import render, redirect
from core.models import Recipe
from .weather import get_weather
from .translate import translate, translate_many, LANGUAGES, TRANSLATION_CACHE

# Keep category headers
CATEGORY_HEADERS = {
    "Entree": "Entrees",
    "Side": "Sides",
    "Appetizer": "Appetizers",
    "Drink": "Drinks"
}

def _cycle_lang(current: str) -> str:
    """
    Return the next language in the LANGUAGES list after the current one.

    Args:
        current (str): The current language code.

    Returns:
        str: The next language code. Defaults to "en" if current is not valid.
    """
    if current in LANGUAGES:
        idx = LANGUAGES.index(current)
        return LANGUAGES[(idx + 1) % len(LANGUAGES)]
    return "en"


def cycle_language(request):
    """
    Cycle the menu language stored in session and redirect back to previous page.

    This view updates `request.session['menu_lang']` to the next language in the
    LANGUAGES list (or an explicitly requested language). Redirects to the URL
    specified in 'next' GET parameter, HTTP_REFERER, or the homepage '/' if neither
    is available.

    Args:
        request (HttpRequest): The Django request object.

    Returns:
        HttpResponseRedirect: Redirects the user to the next URL.
    """
    current = request.session.get("menu_lang", "en")
    lang_param = request.GET.get("lang")

    if lang_param == "next" or lang_param is None:
        # Preserve legacy behavior: clicking the logo cycles to the next language
        new_lang = _cycle_lang(current)
    elif lang_param in LANGUAGES:
        # Explicit selection from a modal/dropdown
        new_lang = lang_param
    else:
        # Fallback to current language if param is invalid
        new_lang = current

    request.session["menu_lang"] = new_lang
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)


def menu_board(request):
    """
    Display the menu board with recipes, weather, and translated labels.

    Determines the display language from session or GET parameters, fetches active
    recipes from the database, translates item names, category headers, menu labels,
    and weather description, then renders the 'menu/menu_board.html' template.

    Args:
        request (HttpRequest): The Django request object.

    Returns:
        HttpResponse: Rendered HTML page with menu items, weather, and translations.

    Notes:
        - Uses `translate` and `translate_many` from the translate module.
        - Uses `get_weather` from the weather module.
        - Stores selected language in `request.session['menu_lang']`.
    """
    # Determine language, stored in session; clicking logo cycles (?lang=next)
    lang_param = request.GET.get("lang")
    current_lang = request.session.get("menu_lang", "en")
    if lang_param == "next":
        lang = _cycle_lang(current_lang)
    elif lang_param in LANGUAGES:
        lang = lang_param
    else:
        lang = current_lang
    request.session["menu_lang"] = lang

    # Fetch menu items
    menu = {
        "Entree": Recipe.objects.filter(type="Entree", active=True),
        "Side": Recipe.objects.filter(type="Side", active=True),
        "Appetizer": Recipe.objects.filter(type="Appetizer", active=True),
        "Drink": Recipe.objects.filter(type="Drink", active=True),
    }

    # Batch translate menu item names
    item_names = {item.name for items in menu.values() for item in items}
    name_map = translate_many(item_names, lang)
    for items in menu.values():
        for item in items:
            item.translated_name = name_map.get(item.name, item.name)

    # Translate category headers and labels in batch
    header_map = translate_many(CATEGORY_HEADERS.values(), lang)
    translated_headers = {k: header_map.get(v, v) for k, v in CATEGORY_HEADERS.items()}

    # Translate weather
    weather = get_weather()
    weather["weather_description"] = translate(weather["weather_description"], lang)

    # Translate hardcoded menu labels
    menu_labels = {
        "meal_options": translate("Meal Options", lang),
        "bowl": translate("Bowl - $8.50", lang),
        "bowl_desc": translate("1 entrée & 1 side", lang),
        "plate": translate("Plate - $10.10", lang),
        "plate_desc": translate("2 entrées & 1 side", lang),
        "bigger_plate": translate("Bigger Plate - $11.70", lang),
        "bigger_plate_desc": translate("3 entrées & 1 side", lang),
        "panda_cub": translate("Panda Cub Meal - $6.80", lang),
        "panda_cub_desc": translate("1 Jr entrée, 1 Jr side, fruit cup & bottle", lang),
        "family_meal": translate("Family Meal - $40.00", lang),
        "family_meal_desc": translate("2 large sides & 3 large entrées", lang),
        "a_la_carte": translate("A la Carte", lang),
        "entree": translate("Entrée", lang),
        "side": translate("Side", lang),
        "small": translate("Small", lang),
        "medium": translate("Medium", lang),
        "large": translate("Large", lang),
        "premium_note": translate("+ $1.90 for premium entrées", lang),
        "no_entrees": translate("No entrees available.", lang),
        "no_sides": translate("No sides available.", lang),
        "no_appetizers": translate("No appetizers available.", lang),
        "no_drinks": translate("No drinks available.", lang),
    }

    return render(request, "menu/menu_board.html", {
        "menu": menu,
        "weather": weather,
        "category_names": translated_headers,
        "menu_labels": menu_labels,
        "lang": lang
    })
