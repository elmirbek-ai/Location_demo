from __future__ import annotations

import os

import httpx


OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


class WeatherServiceError(Exception):
    """Raised when weather data cannot be retrieved or validated."""


class WeatherServiceConfigurationError(WeatherServiceError):
    """Raised when the OpenWeather API key is missing."""


def get_api_key() -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not api_key:
        raise WeatherServiceConfigurationError("OPENWEATHER_API_KEY is not configured")
    return api_key


def parse_weather_payload(payload: object) -> dict[str, float | str | None]:
    if not isinstance(payload, dict):
        raise WeatherServiceError("Weather service returned a non-object response")

    main_data = payload.get("main")
    if not isinstance(main_data, dict):
        raise WeatherServiceError("Weather service response has no main data")

    temperature = main_data.get("temp")
    humidity = main_data.get("humidity")
    if (
        not isinstance(temperature, (int, float))
        or isinstance(temperature, bool)
        or not isinstance(humidity, (int, float))
        or isinstance(humidity, bool)
        or not 0 <= humidity <= 100
    ):
        raise WeatherServiceError("Weather service returned invalid measurements")

    city = payload.get("name")
    if not isinstance(city, str) or not city.strip():
        city = None

    return {
        "temperature": float(temperature),
        "humidity": float(humidity),
        "city": city,
    }


async def _fetch_weather(
    lat: float,
    lon: float,
    client: httpx.AsyncClient,
) -> dict[str, float | str | None]:
    try:
        response = await client.get(
            OPENWEATHER_URL,
            params={
                "lat": lat,
                "lon": lon,
                "appid": get_api_key(),
                "units": "metric",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as error:
        raise WeatherServiceError("Weather service timed out") from error
    except httpx.HTTPStatusError as error:
        raise WeatherServiceError("Weather service returned an HTTP error") from error
    except httpx.RequestError as error:
        raise WeatherServiceError("Weather service request failed") from error
    except ValueError as error:
        raise WeatherServiceError("Weather service returned invalid JSON") from error

    return parse_weather_payload(payload)


async def get_weather(
    lat: float,
    lon: float,
    client: httpx.AsyncClient | None = None,
) -> dict[str, float | str | None]:
    if client is not None:
        return await _fetch_weather(lat, lon, client)

    async with httpx.AsyncClient() as async_client:
        return await _fetch_weather(lat, lon, async_client)
