"""
Module apps.kitchen.weather

Provides functions to fetch and cache weather information for the kitchen app.

Functions:
- get_weather(): Retrieves the current weather for College Station, using
  caching to avoid excessive API calls.

Cache:
- The weather data is cached in a JSON file `weather_cache.json` for 10 minutes.


"""

from django.conf import settings
import requests
import json
import os
import time

CACHE_FILE = os.path.join(os.path.dirname(__file__), "weather_cache.json")
CACHE_DURATION = 10 * 60  # 10 minutes


def get_weather():
    """
    Fetch the current weather for College Station.

    The function uses a cached JSON file to avoid repeated API requests. If the cache
    is older than CACHE_DURATION (10 minutes), a new request is made to the
    OpenWeatherMap API.

    Returns:
        dict: A dictionary containing:
            - timestamp (float): The UNIX timestamp of when the data was fetched.
            - city (str): The city name ("College Station").
            - weather_description (str): A brief description of the current weather.
            - temperature (float or str): Current temperature in Fahrenheit, or "N/A" if unavailable.
            - icon (str or None): Weather icon code from OpenWeatherMap, or None if unavailable.

    Notes:
        - Requires `EXTERNAL_API_KEY` in Django settings.
        - Returns default error data if API call fails or API key is missing.
    """
    city = "College Station"

    # Load cache if still fresh
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
        if time.time() - cache.get("timestamp", 0) < CACHE_DURATION:
            return cache

    api_key = getattr(settings, "EXTERNAL_API_KEY", "")
    if not api_key:
        return {
            "city": city,
            "weather_description": "Error retrieving weather",
            "temperature": "N/A",
            "icon": None,
        }

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        weather_description = data["weather"][0]["description"]
        icon = data["weather"][0]["icon"]
        temperature = data["main"]["temp"]

        weather_info = {
            "timestamp": time.time(),
            "city": city,
            "weather_description": weather_description,
            "temperature": temperature,
            "icon": icon,
        }

        with open(CACHE_FILE, "w") as f:
            json.dump(weather_info, f)

        return weather_info

    except Exception:
        return {
            "city": city,
            "weather_description": "Error retrieving weather",
            "temperature": "N/A",
            "icon": None,
        }
