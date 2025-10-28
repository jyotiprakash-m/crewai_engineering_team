import unittest
from unittest.mock import Mock, patch
import requests

from Weather import Weather


class TestWeatherModule(unittest.TestCase):
    def setUp(self):
        # use a dummy API key for tests
        self.api_key = "TESTKEY"

    def make_mock_response(self, json_data=None, status_code=200, json_side_effect=None, raise_for_status_side_effect=None):
        resp = Mock()
        resp.status_code = status_code
        if json_side_effect is not None:
            resp.json.side_effect = json_side_effect
        else:
            resp.json.return_value = json_data
        if raise_for_status_side_effect is not None:
            resp.raise_for_status.side_effect = raise_for_status_side_effect
        else:
            # default: no exception
            resp.raise_for_status.return_value = None
        return resp

    def test_init_invalid_api_key_empty(self):
        with self.assertRaises(ValueError):
            Weather(api_key="")

    def test_init_invalid_api_key_non_string(self):
        with self.assertRaises(ValueError):
            Weather(api_key=123)

    def test_parse_weather_data_valid(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        raw = {
            "main": {"temp": 15.5, "humidity": 80},
            "weather": [{"description": "light rain"}],
            "name": "Test City",
        }
        parsed = w.parse_weather_data(raw)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["temperature"], 15.5)
        self.assertEqual(parsed["humidity"], 80)
        self.assertEqual(parsed["description"], "light rain")
        self.assertEqual(parsed["city"], "Test City")

    def test_parse_weather_data_non_dict(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        with self.assertRaises(KeyError):
            w.parse_weather_data([1, 2, 3])

    def test_parse_weather_data_missing_main(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        raw = {"weather": [{"description": "x"}], "name": "X"}
        with self.assertRaises(KeyError):
            w.parse_weather_data(raw)

    def test_parse_weather_data_missing_weather(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        raw = {"main": {"temp": 10, "humidity": 50}, "name": "X"}
        with self.assertRaises(KeyError):
            w.parse_weather_data(raw)

    def test_make_api_request_network_error(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        # simulate network exception from requests
        w.session.get = Mock(side_effect=requests.exceptions.RequestException("fail"))
        with self.assertRaises(ConnectionError) as cm:
            w.make_api_request("http://example.com", params={})
        self.assertIn("Failed to connect to weather service", str(cm.exception))

    def test_make_api_request_non_json_with_http_error(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        # json() raises ValueError, raise_for_status raises HTTPError
        http_err = requests.exceptions.HTTPError("404 Not Found")
        resp = self.make_mock_response(json_data=None, status_code=404, json_side_effect=ValueError("No JSON"), raise_for_status_side_effect=http_err)
        w.session.get = Mock(return_value=resp)
        with self.assertRaises(ConnectionError) as cm:
            w.make_api_request("http://example.com", params={})
        self.assertIn("Weather API HTTP error", str(cm.exception))

    def test_make_api_request_non_json_no_http_error(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        # json() raises ValueError, raise_for_status does not raise
        resp = self.make_mock_response(json_data=None, status_code=200, json_side_effect=ValueError("No JSON"), raise_for_status_side_effect=None)
        w.session.get = Mock(return_value=resp)
        with self.assertRaises(ConnectionError) as cm:
            w.make_api_request("http://example.com", params={})
        self.assertIn("Unexpected non-JSON response", str(cm.exception))

    def test_make_api_request_status_not_200_with_json(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        data = {"message": "bad request"}
        resp = self.make_mock_response(json_data=data, status_code=400)
        w.session.get = Mock(return_value=resp)
        with self.assertRaises(ConnectionError) as cm:
            w.make_api_request("http://example.com", params={})
        self.assertIn("Weather API error", str(cm.exception))
        self.assertIn("bad request", str(cm.exception))

    def test_get_weather_by_city_invalid_city(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        with self.assertRaises(ValueError):
            w.get_weather_by_city("")

    def test_get_weather_by_city_api_returns_error_cod(self):
        w = Weather(api_key=self.api_key, cache_ttl=0)
        # patch make_api_request to return an error payload
        with patch.object(Weather, 'make_api_request', return_value={"cod": "404", "message": "city not found"}):
            with self.assertRaises(ConnectionError) as cm:
                w.get_weather_by_city("Nowhere")
            self.assertIn("Weather API returned an error", str(cm.exception))

    def test_get_weather_by_city_success_and_caching(self):
        # set cache_ttl > 0 to enable caching
        w = Weather(api_key=self.api_key, cache_ttl=10)

        raw = {
            "cod": 200,
            "main": {"temp": 22.0, "humidity": 55},
            "weather": [{"description": "clear sky"}],
            "name": "CacheCity",
        }

        mock_make = Mock(return_value=raw)
        # patch the instance's make_api_request
        w.make_api_request = mock_make

        # patch time.time to a fixed value so caching uses it
        with patch('Weather.time.time', side_effect=[1000.0, 1000.0]):
            first = w.get_weather_by_city("CacheCity")
            second = w.get_weather_by_city("CacheCity")

        self.assertEqual(first, second)
        # should have called make_api_request only once because second result came from cache
        mock_make.assert_called_once()

    def test_get_weather_by_city_cache_expiry(self):
        # Test that cache expires after ttl
        w = Weather(api_key=self.api_key, cache_ttl=5)
        raw = {
            "cod": 200,
            "main": {"temp": 10.0, "humidity": 30},
            "weather": [{"description": "snow"}],
            "name": "ExpireCity",
        }
        mock_make = Mock(return_value=raw)
        w.make_api_request = mock_make

        # simulate time progression: first call at t=1000, second call at t=1006 (> ttl)
        with patch('Weather.time.time', side_effect=[1000.0, 1006.0]):
            first = w.get_weather_by_city("ExpireCity")
            second = w.get_weather_by_city("ExpireCity")

        # Because the cache expired, make_api_request should have been called twice
        self.assertEqual(mock_make.call_count, 2)
        self.assertEqual(first, second)


if __name__ == '__main__':
    unittest.main()