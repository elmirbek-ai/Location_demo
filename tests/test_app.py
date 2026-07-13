import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

import main
from weather_service import WeatherServiceConfigurationError, WeatherServiceError


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(main.app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def setUp(self):
        main.rate_limiter.clear()
        main.weather_cache.clear()

    def test_home_page_loads_outside_project_directory(self):
        original_directory = Path.cwd()
        try:
            os.chdir(main.BASE_DIRECTORY.parent)
            response = self.client.get("/")
        finally:
            os.chdir(original_directory)

        self.assertEqual(response.status_code, 200)
        self.assertIn("AgroAI климаттык жардамчы", response.text)

    def test_valid_location_returns_weather_and_combined_recommendation(self):
        weather = {"temperature": 40, "humidity": 90, "city": "Bishkek"}
        with patch("main.get_weather", new=AsyncMock(return_value=weather)):
            response = self.client.post(
                "/location",
                json={"lat": 42.87, "lon": 74.6},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Грибок", response.json()["recommendation"])
        self.assertIn("сугаруу", response.json()["recommendation"])

    def test_missing_or_out_of_range_coordinates_return_422(self):
        invalid_payloads = (
            {},
            {"lat": None, "lon": None},
            {"lat": 91, "lon": 74.6},
            {"lat": 42.87, "lon": -181},
            {"lat": "42.87", "lon": 74.6},
        )

        for payload in invalid_payloads:
            with self.subTest(payload=payload):
                response = self.client.post("/location", json=payload)
                self.assertEqual(response.status_code, 422)

    def test_service_errors_return_generic_502(self):
        provider_error = "private provider detail"
        with patch(
            "main.get_weather",
            new=AsyncMock(side_effect=WeatherServiceError(provider_error)),
        ):
            response = self.client.post(
                "/location",
                json={"lat": 42.87, "lon": 74.6},
            )

        self.assertEqual(response.status_code, 502)
        self.assertNotIn(provider_error, response.text)

    def test_missing_configuration_returns_503(self):
        with patch(
            "main.get_weather",
            new=AsyncMock(side_effect=WeatherServiceConfigurationError("secret")),
        ):
            response = self.client.post(
                "/location",
                json={"lat": 42.87, "lon": 74.6},
            )

        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.text)

    def test_same_location_uses_cache(self):
        weather = {"temperature": 20, "humidity": 50, "city": "Bishkek"}
        service = AsyncMock(return_value=weather)
        with patch("main.get_weather", new=service):
            first = self.client.post(
                "/location",
                json={"lat": 42.87, "lon": 74.6},
            )
            second = self.client.post(
                "/location",
                json={"lat": 42.87, "lon": 74.6},
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(service.await_count, 1)

    def test_rate_limit_returns_429(self):
        original_limiter = main.rate_limiter
        main.rate_limiter = main.RateLimiter(max_requests=2, window_seconds=60)
        weather = {"temperature": 20, "humidity": 50, "city": "Bishkek"}
        try:
            with patch("main.get_weather", new=AsyncMock(return_value=weather)):
                responses = [
                    self.client.post(
                        "/location",
                        json={"lat": 42.87, "lon": 74.6},
                    )
                    for _ in range(3)
                ]
        finally:
            main.rate_limiter = original_limiter

        self.assertEqual([response.status_code for response in responses], [200, 200, 429])

    def test_frontend_does_not_use_inner_html(self):
        template = (main.BASE_DIRECTORY / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("innerHTML", template)
        self.assertIn("textContent", template)
        self.assertIn("handleLocationError", template)


if __name__ == "__main__":
    unittest.main()
