from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import mimetypes
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from .errors import StarBridgeError


class CloudAPIError(StarBridgeError):
    """A cloud service rejected a request or returned malformed data."""


@dataclass(frozen=True, slots=True)
class TimeAPIResult:
    datetime: datetime
    timezone: str
    unix_time: int


@dataclass(frozen=True, slots=True)
class WeatherReading:
    temperature_c: float | None
    humidity_percent: float | None
    apparent_temperature_c: float | None
    precipitation_mm: float | None
    weather_code: int | None
    wind_speed_kmh: float | None
    observed_at: str | None
    timezone: str


class CloudClient:
    """Host-side HTTPS clients. API keys remain on the computer, not in firmware."""

    def __init__(self, timeout: float = 30.0, opener: Any = None) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.timeout = timeout
        self._opener = opener or urlopen

    def _request(self, request: Request) -> dict[str, Any]:
        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:500]
            raise CloudAPIError(f"cloud API returned HTTP {error.code}: {detail}") from error
        except (URLError, OSError) as error:
            raise CloudAPIError(f"cloud API connection failed: {error}") from error
        try:
            result = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CloudAPIError("cloud API returned invalid JSON") from error
        if not isinstance(result, dict):
            raise CloudAPIError("cloud API returned an unexpected JSON value")
        return result

    def time(self, timezone_name: str = "Asia/Shanghai", *,
             base_url: str = "https://worldtimeapi.org/api") -> TimeAPIResult:
        url = f"{base_url.rstrip('/')}/timezone/{quote(timezone_name, safe='/')}"
        data = self._request(Request(url, headers={"User-Agent": "StarBridge/4.5"}))
        try:
            return TimeAPIResult(
                datetime.fromisoformat(str(data["datetime"])),
                str(data["timezone"]), int(data["unixtime"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise CloudAPIError("time API response is missing required fields") from error

    def weather(self, latitude: float, longitude: float, *, timezone_name: str = "auto",
                base_url: str = "https://api.open-meteo.com/v1/forecast") -> WeatherReading:
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("latitude/longitude are out of range")
        fields = (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "precipitation,weather_code,wind_speed_10m"
        )
        query = urlencode({"latitude": latitude, "longitude": longitude,
                           "current": fields, "timezone": timezone_name})
        data = self._request(Request(f"{base_url}?{query}",
                                     headers={"User-Agent": "StarBridge/4.5"}))
        current = data.get("current")
        if not isinstance(current, dict):
            raise CloudAPIError("weather API response is missing current conditions")
        return WeatherReading(
            _optional_float(current.get("temperature_2m")),
            _optional_float(current.get("relative_humidity_2m")),
            _optional_float(current.get("apparent_temperature")),
            _optional_float(current.get("precipitation")),
            _optional_int(current.get("weather_code")),
            _optional_float(current.get("wind_speed_10m")),
            str(current["time"]) if current.get("time") is not None else None,
            str(data.get("timezone", timezone_name)),
        )

    def chat(self, prompt: str, *, api_key: str | None = None,
             model: str = "gpt-4o-mini", system: str | None = None,
             base_url: str = "https://api.openai.com/v1") -> str:
        key = _api_key(api_key)
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        body = json.dumps({"model": model, "messages": messages}).encode("utf-8")
        data = self._request(Request(
            f"{base_url.rstrip('/')}/chat/completions", data=body, method="POST",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                     "User-Agent": "StarBridge/4.5"},
        ))
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise CloudAPIError("language model response is missing message content") from error
        if not isinstance(content, str):
            raise CloudAPIError("language model returned non-text content")
        return content

    def transcribe(self, audio_file: str | Path, *, api_key: str | None = None,
                   model: str = "gpt-4o-mini-transcribe", language: str | None = None,
                   base_url: str = "https://api.openai.com/v1") -> str:
        path = Path(audio_file)
        audio = path.read_bytes()
        boundary = f"starbridge-{uuid4().hex}"
        fields = {"model": model}
        if language:
            fields["language"] = language
        parts: list[bytes] = []
        for name, value in fields.items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                f"{value}\r\n".encode("utf-8")
            )
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{path.name}\"\r\nContent-Type: {media_type}\r\n\r\n".encode("utf-8")
            + audio + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode("ascii"))
        data = self._request(Request(
            f"{base_url.rstrip('/')}/audio/transcriptions", data=b"".join(parts), method="POST",
            headers={"Authorization": f"Bearer {_api_key(api_key)}",
                     "Content-Type": f"multipart/form-data; boundary={boundary}",
                     "User-Agent": "StarBridge/4.5"},
        ))
        text = data.get("text")
        if not isinstance(text, str):
            raise CloudAPIError("transcription response is missing text")
        return text


def _api_key(explicit: str | None) -> str:
    key = explicit or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise CloudAPIError("set OPENAI_API_KEY or pass api_key explicitly")
    return key


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)
