""" 
Weather.py

A self-contained Weather module implementing a Weather class that fetches current weather
information for a given city name using the OpenWeatherMap API.

Usage:
    from Weather import Weather, APIError
    w = Weather(api_key="YOUR_API_KEY_HERE")
    info = w.get_weather_by_city("London")

This module does not include any UI. It raises ValueError for invalid city names,
ConnectionError for network issues, and APIError for API-related issues.
"""

import re
from typing import Dict, Any

import requests


class APIError(Exception):
    """Custom exception to indicate API-related errors or unexpected response formats."""


class Weather:
    """Weather client to fetch current weather by city name.

    This implementation uses OpenWeatherMap's current weather API. The provided API key
    must be valid for requests to succeed.
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openweathermap.org/data/2.5/weather", timeout: int = 10, retries: int = 1) -> None:
        """Initialize the Weather client.

        Parameters:
            api_key: API key string for the weather service.
            base_url: Base URL for the weather API endpoint.
            timeout: Request timeout in seconds.
            retries: Number of retry attempts for transient network errors.
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("api_key must be a non-empty string")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = max(0, int(retries))

    def validate_city_name(self, city_name: str) -> bool:
        """Validate the provided city name.

        A valid city name per the design: non-empty and may include alphabets and spaces.

        Parameters:
            city_name: City name string to validate.

        Returns:
            True if valid, False otherwise.
        """
        if not city_name or not isinstance(city_name, str):
            return False

        city_name = city_name.strip()
        if not city_name:
            return False

        # Only allow letters and spaces as specified in the design
        return bool(re.fullmatch(r"[A-Za-z ]+", city_name))

    def parse_weather_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract and format relevant weather information from API response.

        Expected returned dictionary structure:
            {
                "city": "City Name",
                "temperature": "25°C",
                "humidity": "60%",
                "conditions": "Clear",
                "wind_speed": "5 km/h"
            }

        Raises APIError if the response structure is not as expected.
        """
        try:
            city = data.get("name")
            if not city:
                # Sometimes API may omit name for some results
                raise KeyError("missing city name")

            main = data["main"]
            temp = main["temp"]  # expected in Celsius if units=metric
            humidity = main["humidity"]

            weather_list = data.get("weather")
            if not weather_list or not isinstance(weather_list, list):
                raise KeyError("missing weather information")

            conditions = weather_list[0].get("description", "").capitalize()

            wind_info = data.get("wind", {})
            wind_speed_m_s = float(wind_info.get("speed", 0.0))
            wind_speed_kmh = wind_speed_m_s * 3.6

            result = {
                "city": str(city),
                "temperature": f"{round(float(temp), 1)}°C",
                "humidity": f"{int(humidity)}%",
                "conditions": conditions,
                "wind_speed": f"{round(wind_speed_kmh, 1)} km/h",
            }
            return result
        except (KeyError, TypeError, ValueError) as exc:
            raise APIError(f"Unexpected API response format: {exc}") from exc

    def get_weather_by_city(self, city_name: str) -> Dict[str, str]:
        """Retrieve weather information for the specified city.

        Parameters:
            city_name: Name of the city to fetch weather for.

        Returns:
            A dictionary containing formatted weather data.

        Exceptions:
            ValueError: If the city name is invalid or empty.
            ConnectionError: If the API cannot be reached.
            APIError: For issues with the response from the weather service.
        """
        if not self.validate_city_name(city_name):
            raise ValueError("Invalid city name. City names must contain only letters and spaces and must not be empty.")

        params = {
            "q": city_name.strip(),
            "appid": self.api_key,
            "units": "metric",
        }

        last_exc = None
        for attempt in range(self.retries + 1):
            try:
                response = requests.get(self.base_url, params=params, timeout=self.timeout)
            except requests.exceptions.RequestException as exc:
                last_exc = exc
                # On network errors, retry if attempts remain
                if attempt < self.retries:
                    continue
                raise ConnectionError(f"Network error while contacting weather service: {exc}") from exc

            # Check HTTP response
            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as exc:
                    raise APIError(f"Invalid JSON response: {exc}") from exc

                return self.parse_weather_data(data)
            elif response.status_code == 401:
                raise APIError("Unauthorized: API key is invalid or missing")
            elif response.status_code == 404:
                # API indicates city not found
                raise APIError("City not found")
            else:
                # For other HTTP errors, include body for debugging
                body = response.text
                raise APIError(f"Weather API error (status {response.status_code}): {body}")

        # If we exhausted retries and fell through, raise connection error
        raise ConnectionError(f"Failed to contact weather service after {self.retries + 1} attempts")


# Module exports
__all__ = ["Weather", "APIError"]