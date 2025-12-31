#!/usr/bin/env python
"""
Quick helper to push sample orders into the kitchen WebSocket.

Usage:
    pip install websocket-client
    python scripts/send_test_orders.py
"""
import json
import random
import time
from datetime import datetime

from websocket import create_connection


ENTREES = [
    "Orange Chicken",
    "Beijing Beef",
    "Kung Pao Chicken",
    "Mushroom Chicken",
    "Black Pepper Chicken",
    "Broccoli Beef",
    "String Bean Chicken Breast",
]

SIDES = ["Chow Mein", "Fried Rice", "Super Greens", "White Rice"]
DRINKS = ["Coca Cola", "Diet Coke", "Sprite", "Dr Pepper"]
APPS = ["Veggie Spring Roll", "Cream Cheese Rangoon", "Chicken Egg Roll"]


def _random_meal(meal_type):
    entree_count = {"bowl": 1, "plate": 2, "bigger-plate": 3}[meal_type]
    side_required = {"bowl": 1, "plate": 1, "bigger-plate": 1}[meal_type]
    entrees = random.sample(ENTREES, entree_count)
    side_choices = random.sample(SIDES, side_required)
    return {"category": "meal", "meal_type": meal_type, "entrees": entrees, "side": side_choices}


def _random_items():
    items = []
    # Always add one meal (random size)
    meal_type = random.choice(["bowl", "plate", "bigger-plate"])
    items.append(_random_meal(meal_type))

    # 50% chance to add a drink
    if random.random() < 0.5:
        items.append({"category": "drink", "name": random.choice(DRINKS), "size": random.choice(["S", "M", "L"])})

    # 40% chance to add an appetizer
    if random.random() < 0.4:
        items.append({"category": "appetizer", "name": random.choice(APPS), "size": random.choice(["S", "M", "L"])})

    return items


def main():
    ws_url = "ws://127.0.0.1:8000/ws/orders/"
    ws = create_connection(ws_url)
    print(f"Connected to {ws_url}")

    for idx in range(1, 16):
        payload = {
            "order_id": random.randint(10_000, 99_999),
            "items": _random_items(),
            "status": "pending",
            "sent_at": datetime.utcnow().isoformat() + "Z",
        }
        ws.send(json.dumps(payload))
        print(f"Sent order {idx}: {payload['order_id']}")
        # Tiny pause so the kitchen view has time to render each separately
        time.sleep(0.25)

    ws.close()
    print("All test orders sent. WebSocket closed.")


if __name__ == "__main__":
    main()
