"""Weather.py

A self-contained module that provides a Weather class to fetch current weather by city name
(using OpenWeatherMap API).

Usage:
    from Weather import Weather
    w = Weather(api_key="YOUR_API_KEY")
    result = w.get_weather_by_city("London")

This module does not perform any UI operations.
"""
from typing import Dict, Any, Optional, Tuple
import requests
import time


class Weather:
    """A class to fetch and parse current weather information by city name.

    This implementation is compatible with the OpenWeatherMap current weather API.
    Provide an API key when creating an instance.

    Example:
        w = Weather(api_key="YOUR_KEY_HERE")
        data = w.get_weather_by_city("Paris")
    """

    DEFAULT_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 10, cache_ttl: int = 300) -> None:
        """Initialize the Weather client.

        Parameters:
            api_key: API key for the weather service (OpenWeatherMap).
            base_url: Optional custom endpoint. Defaults to OpenWeatherMap current weather endpoint.
            timeout: Request timeout in seconds.
            cache_ttl: Time-to-live for in-memory cache in seconds. Set to 0 to disable caching.
        """
        if not isinstance(api_key, str) or api_key.strip() == "":
            raise ValueError("api_key must be a non-empty string")
        self.api_key = api_key.strip()
        self.base_url = base_url or self.DEFAULT_ENDPOINT
        self.timeout = int(timeout)
        self.session = requests.Session()
        self._cache_ttl = int(cache_ttl) if cache_ttl is not None else 0
        # _cache maps (city_lower, units) -> (timestamp, parsed_result)
        self._cache: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}

    def make_api_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a GET request to the specified endpoint with given params.

        Raises ConnectionError on network issues or unexpected HTTP responses.
        """
        try:
            resp = self.session.get(endpoint, params=params, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to weather service: {e}")

        # Try to parse JSON even on non-200 to provide helpful error messages
        try:
            data = resp.json()
        except ValueError:
            # Non-JSON response
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise ConnectionError(f"Weather API HTTP error: {e}")
            # If raise_for_status did not raise, raise a generic ConnectionError
            raise ConnectionError("Unexpected non-JSON response from weather service")

        if resp.status_code != 200:
            # API often returns JSON with 'message' on error
            msg = data.get("message") if isinstance(data, dict) else None
            raise ConnectionError(f"Weather API error (status {resp.status_code}): {msg or data}")

        return data

    def parse_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse the raw JSON data from the weather API and return structured info.

        Expected return format:
            {
                "temperature": float,
                "humidity": int,
                "description": str,
                "city": str
            }

        Raises KeyError if expected keys are missing.
        """
        if not isinstance(data, dict):
            raise KeyError("Expected data to be a dict")

        # Validate presence of required keys
        if "main" not in data:
            raise KeyError("Missing 'main' in weather data")
        if "weather" not in data:
            raise KeyError("Missing 'weather' in weather data")

        main = data["main"]
        weather_list = data["weather"]

        if not isinstance(main, dict):
            raise KeyError("'main' must be a dict")
        if not isinstance(weather_list, list) or len(weather_list) == 0:
            raise KeyError("'weather' must be a non-empty list")

        try:
            temperature = float(main["temp"])
            humidity = int(main["humidity"])
            description = str(weather_list[0].get("description", "")).strip()
            city = str(data.get("name", "")).strip()
        except KeyError as e:
            raise KeyError(f"Missing expected key in weather data: {e}")
        except (TypeError, ValueError) as e:
            raise KeyError(f"Unexpected data type in weather data: {e}")

        return {
            "temperature": temperature,
            "humidity": humidity,
            "description": description,
            "city": city,
        }

    def get_weather_by_city(self, city_name: str, units: str = "metric") -> Dict[str, Any]:
        """Retrieve current weather for the given city name.

        Parameters:
            city_name: Name of the city to query.
            units: Units for temperature. "metric" for Celsius, "imperial" for Fahrenheit, or "standard" for Kelvin.

        Returns:
            A dict with keys: temperature (float), humidity (int), description (str), city (str).

        Raises:
            ValueError: If city_name is empty or invalid.
            ConnectionError: If there's a problem connecting to or with the API.
            KeyError: If expected fields are missing in the API response.
        """
        if not isinstance(city_name, str) or city_name.strip() == "":
            raise ValueError("city_name must be a non-empty string")
        city_key = city_name.strip()

        cache_key = (city_key.lower(), units)
        if self._cache_ttl > 0:
            entry = self._cache.get(cache_key)
            if entry:
                timestamp, cached_result = entry
                if time.time() - timestamp <= self._cache_ttl:
                    return cached_result
                else:
                    # expired
                    del self._cache[cache_key]

        params = {
            "q": city_key,
            "appid": self.api_key,
            "units": units,
        }

        raw = self.make_api_request(self.base_url, params)

        # Some APIs return error codes as strings or numbers inside JSON; handle that
        cod = raw.get("cod")
        if cod is not None:
            # cod can be str or int
            try:
                cod_int = int(cod)
            except (TypeError, ValueError):
                cod_int = None
            if cod_int is not None and cod_int != 200:
                msg = raw.get("message", "Unknown error from weather API")
                raise ConnectionError(f"Weather API returned an error: {msg}")

        parsed = self.parse_weather_data(raw)

        if self._cache_ttl > 0:
            self._cache[cache_key] = (time.time(), parsed)

        return parsed


# Module does not execute any network calls when imported.
# Example usage (not executed here):
# from Weather import Weather
# w = Weather(api_key="YOUR_KEY")
# print(w.get_weather_by_city("London"))