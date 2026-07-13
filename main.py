from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from threading import Lock
from time import monotonic

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError

from recommendation import recommend
from weather_service import (
    WeatherServiceConfigurationError,
    WeatherServiceError,
    get_weather,
)


BASE_DIRECTORY = Path(__file__).resolve().parent
CACHE_TTL_SECONDS = 300
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60

app = FastAPI(title="AgroAI Location Demo")
templates = Jinja2Templates(directory=str(BASE_DIRECTORY / "templates"))


class LocationPayload(BaseModel):
    lat: float = Field(ge=-90, le=90, strict=True)
    lon: float = Field(ge=-180, le=180, strict=True)


class WeatherData(BaseModel):
    temperature: float
    humidity: float = Field(ge=0, le=100)
    city: str | None = None


class LocationResponse(BaseModel):
    weather: WeatherData
    recommendation: str


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client_id: str) -> bool:
        now = monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = self._requests[client_id]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()
            if len(timestamps) >= self.max_requests:
                return False
            timestamps.append(now)
            return True

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()


class WeatherCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._values: dict[
            tuple[float, float],
            tuple[float, dict[str, float | str | None]],
        ] = {}
        self._lock = Lock()

    def get(self, key: tuple[float, float]) -> dict[str, float | str | None] | None:
        now = monotonic()
        with self._lock:
            cached = self._values.get(key)
            if cached is None:
                return None
            expires_at, value = cached
            if expires_at <= now:
                self._values.pop(key, None)
                return None
            return value.copy()

    def set(
        self,
        key: tuple[float, float],
        value: dict[str, float | str | None],
    ) -> None:
        with self._lock:
            self._values[key] = (monotonic() + self.ttl_seconds, value.copy())

    def clear(self) -> None:
        with self._lock:
            self._values.clear()


rate_limiter = RateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
weather_cache = WeatherCache(CACHE_TTL_SECONDS)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/location", response_model=LocationResponse)
async def receive_location(payload: LocationPayload, request: Request) -> LocationResponse:
    client_id = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Өтө көп суроо жөнөтүлдү. Бир аздан кийин кайра аракет кылыңыз.",
        )

    cache_key = (round(payload.lat, 4), round(payload.lon, 4))
    weather_payload = weather_cache.get(cache_key)

    if weather_payload is None:
        try:
            weather_payload = await get_weather(payload.lat, payload.lon)
        except WeatherServiceConfigurationError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Аба ырайы кызматы азырынча конфигурацияланган эмес.",
            ) from error
        except WeatherServiceError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Аба ырайы кызматынан маалымат алуу мүмкүн болгон жок.",
            ) from error

        weather_cache.set(cache_key, weather_payload)

    try:
        weather = WeatherData.model_validate(weather_payload)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Аба ырайы кызматы туура эмес маалымат кайтарды.",
        ) from error

    return LocationResponse(
        weather=weather,
        recommendation=recommend(weather.model_dump()),
    )
