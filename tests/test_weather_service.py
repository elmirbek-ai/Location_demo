import os
import unittest
from unittest.mock import patch

import httpx

from weather_service import (
    WeatherServiceConfigurationError,
    WeatherServiceError,
    get_weather,
    parse_weather_payload,
)


class WeatherPayloadTests(unittest.TestCase):
    def test_parses_valid_payload(self):
        self.assertEqual(
            parse_weather_payload(
                {
                    "main": {"temp": 18.5, "humidity": 60},
                    "name": "Bishkek",
                }
            ),
            {"temperature": 18.5, "humidity": 60.0, "city": "Bishkek"},
        )

    def test_rejects_missing_or_invalid_measurements(self):
        invalid_payloads = (
            {},
            {"main": {}},
            {"main": {"temp": "hot", "humidity": 50}},
            {"main": {"temp": 20, "humidity": 150}},
        )
        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(WeatherServiceError):
                    parse_weather_payload(payload)


class WeatherServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_api_key_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json={"main": {}})
                )
            ) as client:
                with self.assertRaises(WeatherServiceConfigurationError):
                    await get_weather(42.87, 74.6, client)

    async def test_success_uses_encoded_query_parameters(self):
        captured_request = None

        def handler(request):
            nonlocal captured_request
            captured_request = request
            return httpx.Response(
                200,
                json={
                    "main": {"temp": 18.5, "humidity": 60},
                    "name": "Bishkek",
                },
            )

        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-key"}):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                result = await get_weather(42.87, 74.6, client)

        self.assertEqual(result["city"], "Bishkek")
        self.assertEqual(captured_request.url.params["lat"], "42.87")
        self.assertEqual(captured_request.url.params["units"], "metric")

    async def test_http_errors_are_not_exposed(self):
        def handler(request):
            return httpx.Response(401, json={"message": "private provider detail"})

        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-key"}):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with self.assertRaisesRegex(WeatherServiceError, "HTTP error"):
                    await get_weather(42.87, 74.6, client)

    async def test_timeouts_are_converted_to_service_error(self):
        def handler(request):
            raise httpx.ReadTimeout("provider detail", request=request)

        with patch.dict(os.environ, {"OPENWEATHER_API_KEY": "test-key"}):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(handler)
            ) as client:
                with self.assertRaisesRegex(WeatherServiceError, "timed out"):
                    await get_weather(42.87, 74.6, client)


if __name__ == "__main__":
    unittest.main()
