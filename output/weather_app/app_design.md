```markdown
# Design Document for Weather.py

## Overview
The `Weather` module will provide functionality to retrieve the current weather conditions based on a city name. The module will include a main class called `Weather`, which encapsulates the methods needed to fetch and return weather data.

## Main Class: Weather

### Responsibilities
The primary responsibilities of the `Weather` class include:
- Fetching weather data from an external weather API.
- Parsing the received data to extract relevant weather information.
- Providing a user-friendly interface to retrieve weather conditions by city name.

### Methods and Signatures

#### `__init__(self, api_key: str) -> None`
Initializes a new instance of the `Weather` class.

- **Parameters:**
  - `api_key` (str): The API key to authenticate requests to the weather service.

#### `get_weather_by_city(self, city_name: str) -> dict`
Retrieves the current weather condition for a given city.

- **Parameters:**
  - `city_name` (str): The name of the city for which to fetch the weather.
- **Returns:**
  - `dict`: A dictionary containing weather information, which includes:
    - `temperature`: Current temperature in degrees Celsius.
    - `humidity`: Humidity percentage.
    - `description`: Short weather description (e.g., "clear sky").
    - `city`: Name of the city.
- **Raises:**
  - `ValueError`: If `city_name` is empty or not valid.
  - `ConnectionError`: If there is a problem connecting to the weather API.
  - `KeyError`: If the expected data is not present in the API response.

#### `parse_weather_data(self, data: dict) -> dict`
Parses JSON data received from the weather API.

- **Parameters:**
  - `data` (dict): The raw response data retrieved from the weather API.
- **Returns:**
  - `dict`: A dictionary with parsed weather information.
- **Raises:**
  - `KeyError`: If the expected keys are missing in the `data`.

### Data Structures
- **Weather Data Structure**: The data returned from `get_weather_by_city` will be a dictionary structured as follows:
  ```python
  {
      "temperature": float,
      "humidity": int,
      "description": str,
      "city": str
  }
  ```

### Helper Functions
#### `make_api_request(self, endpoint: str, params: dict) -> dict`
Makes an API request to the specified endpoint with the provided parameters.

- **Parameters:**
  - `endpoint` (str): The API endpoint for fetching weather data.
  - `params` (dict): A dictionary of query parameters for the request.
- **Returns:**
  - `dict`: The JSON response from the API.
- **Raises:**
  - `ConnectionError`: If the API request fails.

### Edge Cases and Error Handling
- Validate `city_name` in `get_weather_by_city` to ensure it is not null or whitespace, raising a `ValueError` if invalid.
- Handle possible connectivity issues gracefully within `make_api_request`, providing informative errors.
- When parsing data, implement checks in `parse_weather_data` to ensure the necessary keys exist and raise `KeyError` if they are missing.

### Extensibility
- Consider implementing a caching mechanism for frequent requests to avoid hitting the API limits.
- Allow for support for multiple units (e.g., Fahrenheit, Kelvin) by adding an optional parameter to `get_weather_by_city`.
- Plan for future integration with additional weather data APIs as needed.

```