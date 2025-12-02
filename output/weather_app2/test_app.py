from unittest import TestCase, main
from unittest.mock import patch, Mock
import requests

from Weather import Weather, APIError


class TestWeather(TestCase):
    def test_init_invalid_api_key_empty(self):
        with self.assertRaises(ValueError):
            Weather(api_key="")

    def test_init_invalid_api_key_non_string(self):
        with self.assertRaises(ValueError):
            Weather(api_key=None)

    def test_validate_city_name_valid(self):
        w = Weather(api_key="dummy")
        self.assertTrue(w.validate_city_name("London"))
        self.assertTrue(w.validate_city_name("New York"))
        self.assertTrue(w.validate_city_name("San Francisco"))  # spaces allowed

    def test_validate_city_name_invalid(self):
        w = Weather(api_key="dummy")
        self.assertFalse(w.validate_city_name(""))
        self.assertFalse(w.validate_city_name("  "))
        self.assertFalse(w.validate_city_name("Paris123"))     # digits not allowed
        self.assertFalse(w.validate_city_name("St. Louis"))    # punctuation not allowed
        self.assertFalse(w.validate_city_name(123))            # non-string

    def test_parse_weather_data_success(self):
        w = Weather(api_key="dummy")
        sample = {
            "name": "Testville",
            "main": {"temp": 25.349, "humidity": 60},
            "weather": [{"description": "clear sky"}],
            "wind": {"speed": 5.0},
        }
        result = w.parse_weather_data(sample)
        self.assertEqual(result["city"], "Testville")
        self.assertEqual(result["temperature"], "25.3°C")   # rounded to 1 decimal
        self.assertEqual(result["humidity"], "60%")
        self.assertEqual(result["conditions"], "Clear sky")  # capitalize() applied
        self.assertEqual(result["wind_speed"], "18.0 km/h") # 5 m/s -> 18.0 km/h

    def test_parse_weather_data_missing_name_raises_apierror(self):
        w = Weather(api_key="dummy")
        sample = {
            "main": {"temp": 10, "humidity": 50},
            "weather": [{"description": "rain"}],
        }
        with self.assertRaises(APIError):
            w.parse_weather_data(sample)

    def test_parse_weather_data_missing_weather_raises_apierror(self):
        w = Weather(api_key="dummy")
        sample = {
            "name": "City",
            "main": {"temp": 10, "humidity": 50},
            # missing 'weather'
        }
        with self.assertRaises(APIError):
            w.parse_weather_data(sample)

    def test_parse_weather_data_invalid_types_raises_apierror(self):
        w = Weather(api_key="dummy")
        sample = {
            "name": "City",
            "main": {"temp": "not-a-number", "humidity": "NaN"},
            "weather": [{"description": "sunny"}],
        }
        with self.assertRaises(APIError):
            w.parse_weather_data(sample)

    def test_get_weather_by_city_invalid_name_raises_valueerror(self):
        w = Weather(api_key="dummy")
        with self.assertRaises(ValueError):
            w.get_weather_by_city("New-York")  # hyphen not allowed

    @patch("Weather.requests.get")
    def test_get_weather_by_city_network_error_exhausts_retries(self, mock_get):
        # Simulate requests raising a RequestException on all attempts
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        w = Weather(api_key="dummy", retries=1)
        with self.assertRaises(ConnectionError) as cm:
            w.get_weather_by_city("London")
        self.assertIn("Network error while contacting weather service", str(cm.exception))

    @patch("Weather.requests.get")
    def test_get_weather_by_city_successful_response(self, mock_get):
        # Create a mock successful response
        sample_data = {
            "name": "London",
            "main": {"temp": 12.0, "humidity": 80},
            "weather": [{"description": "overcast clouds"}],
            "wind": {"speed": 2.5},
        }
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_data
        mock_get.return_value = mock_resp

        w = Weather(api_key="dummy")
        result = w.get_weather_by_city("London")
        self.assertEqual(result["city"], "London")
        self.assertEqual(result["temperature"], "12.0°C")
        self.assertEqual(result["humidity"], "80%")
        self.assertEqual(result["conditions"], "Overcast clouds")
        # 2.5 m/s -> 9.0 km/h
        self.assertEqual(result["wind_speed"], "9.0 km/h")

    @patch("Weather.requests.get")
    def test_get_weather_by_city_unauthorized(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_get.return_value = mock_resp

        w = Weather(api_key="badkey")
        with self.assertRaises(APIError) as cm:
            w.get_weather_by_city("London")
        self.assertIn("Unauthorized", str(cm.exception))

    @patch("Weather.requests.get")
    def test_get_weather_by_city_city_not_found(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_resp.text = "city not found"
        mock_get.return_value = mock_resp

        w = Weather(api_key="dummy")
        with self.assertRaises(APIError) as cm:
            w.get_weather_by_city("Atlantis")
        self.assertIn("City not found", str(cm.exception))

    @patch("Weather.requests.get")
    def test_get_weather_by_city_other_http_error(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_get.return_value = mock_resp

        w = Weather(api_key="dummy")
        with self.assertRaises(APIError) as cm:
            w.get_weather_by_city("London")
        self.assertIn("Weather API error (status 500)", str(cm.exception))
        self.assertIn("Internal Server Error", str(cm.exception))

    @patch("Weather.requests.get")
    def test_get_weather_by_city_invalid_json_raises_apierror(self, mock_get):
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("No JSON")
        mock_get.return_value = mock_resp

        w = Weather(api_key="dummy")
        with self.assertRaises(APIError) as cm:
            w.get_weather_by_city("London")
        self.assertIn("Invalid JSON response", str(cm.exception))

    @patch("Weather.requests.get")
    def test_retries_then_successful(self, mock_get):
        # First call raises a network error, second returns a valid response
        sample_data = {
            "name": "RetryCity",
            "main": {"temp": 20.0, "humidity": 50},
            "weather": [{"description": "windy"}],
            "wind": {"speed": 3.0},
        }
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_data

        mock_get.side_effect = [requests.exceptions.ConnectionError("conn err"), mock_resp]

        w = Weather(api_key="dummy", retries=1)
        result = w.get_weather_by_city("RetryCity")
        self.assertEqual(result["city"], "RetryCity")
        self.assertEqual(result["temperature"], "20.0°C")

    @patch("Weather.requests.get")
    def test_get_weather_by_city_strips_spaces_in_params(self, mock_get):
        # Ensure city_name is stripped when building params (indirectly by checking call args)
        sample_data = {
            "name": "TrimCity",
            "main": {"temp": 15.0, "humidity": 40},
            "weather": [{"description": "sunny"}],
            "wind": {"speed": 1.0},
        }
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_data
        mock_get.return_value = mock_resp

        w = Weather(api_key="akey")
        result = w.get_weather_by_city("  TrimCity  ")
        self.assertEqual(result["city"], "TrimCity")
        # verify that requests.get was called with q parameter stripped
        called_args, called_kwargs = mock_get.call_args
        params = called_kwargs.get("params", {})
        self.assertEqual(params.get("q"), "TrimCity")
        self.assertEqual(params.get("appid"), "akey")
        self.assertEqual(params.get("units"), "metric")


if __name__ == "__main__":
    main()