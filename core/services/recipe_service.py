from core.models import Recipe

class RecipeService:

    @staticmethod
    def get_items():
        """Retrieve all menu items."""
        return Recipe.objects.all()

    @staticmethod
    def get_items_by_type(item_type):
        """Filter menu items by type/category."""
        return Recipe.objects.filter(type__iexact=item_type, active=True)

    @staticmethod
    def add_item(name, price, type, ingredients=None):
        """
        Add a menu item and optionally link ingredients.
        ingredients = list of Inventory IDs
        """
        recipe = Recipe.objects.create(name=name, price=price, type=type)

        if ingredients:
            recipe.ingredients.set(ingredients)

        return recipe
