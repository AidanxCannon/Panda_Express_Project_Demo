class MenuItem:
    def __init__(self, id, name, price, type, quantity_sold=0, active=True):
        """
        Represents an individual menu item or product available for sale.

        Args:
            id (int): The unique identifier for the item.
            name (str): The display name of the item.
            price (float): The price of the item.
            type (str): The category or type of the item (e.g., "Drink", "Food").
            quantity_sold (int, optional): Number of units sold. Defaults to 0.
            active (bool, optional): Whether the item is currently active. Defaults to True.
        """
        self.id = id
        self.name = name
        self.price = price
        self.type = type
        self.quantity_sold = quantity_sold
        self.active = active

    # --- Getters ---
    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_price(self):
        return self.price

    def get_type(self):
        return self.type

    def get_quantity_sold(self):
        return self.quantity_sold

    def is_active(self):
        return self.active

    # --- Setters ---
    def set_quantity_sold(self, quantity_sold):
        self.quantity_sold = quantity_sold

    def set_active(self, active):
        self.active = active

    # --- Utility (optional) ---
    def __str__(self):
        return f"MenuItem(id={self.id}, name='{self.name}', price={self.price}, type='{self.type}', sold={self.quantity_sold}, active={self.active})"