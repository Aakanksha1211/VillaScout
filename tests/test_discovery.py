import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from villascout.config import Settings
from villascout.services.discovery.google_places import GooglePlacesError, GooglePlacesSource
from villascout.utils.cache import FileCache


class FakeHttpClient:
    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        _ = headers
        params = params or {}
        if "findplacefromtext" in url:
            return {
                "status": "OK",
                "candidates": [{"geometry": {"location": {"lat": 19.7, "lng": 73.5}}}],
            }
        if "textsearch" in url or "nearbysearch" in url:
            return {
                "status": "OK",
                "results": [{"place_id": "abc123", "name": "Casa Verde"}],
            }
        if "details" in url:
            return {
                "status": "OK",
                "result": {
                    "place_id": params["place_id"],
                    "name": "Casa Verde",
                    "formatted_address": "Lake Road",
                    "formatted_phone_number": "+91 9876543210",
                    "website": "https://example.com",
                    "geometry": {"location": {"lat": 19.7, "lng": 73.5}},
                    "rating": 4.6,
                    "user_ratings_total": 42,
                    "types": ["lodging"],
                },
            }
        raise AssertionError(url)


class DeniedHttpClient:
    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        _ = url, params, headers
        return {
            "status": "REQUEST_DENIED",
            "error_message": "This API project is not authorized to use this API.",
        }


def test_google_places_source_normalizes_results(tmp_path: Path) -> None:
    settings = Settings(google_api_key="test-key", cache_directory=tmp_path)
    source = GooglePlacesSource(
        settings=settings,
        http_client=FakeHttpClient(),  # type: ignore[arg-type]
        cache=FileCache(tmp_path, ttl_seconds=60),
        keywords=["villa"],
    )

    villas = asyncio.run(source.search("Igatpuri", 40_000))

    assert len(villas) == 1
    assert villas[0].name == "Casa Verde"
    assert villas[0].source_listing.external_id == "abc123"
    assert villas[0].review_summary.rating == pytest.approx(4.6)


def test_google_places_source_raises_on_request_denied(tmp_path: Path) -> None:
    settings = Settings(google_api_key="test-key", cache_directory=tmp_path)
    source = GooglePlacesSource(
        settings=settings,
        http_client=DeniedHttpClient(),  # type: ignore[arg-type]
        cache=FileCache(tmp_path, ttl_seconds=60),
        keywords=["villa"],
    )

    with pytest.raises(GooglePlacesError):
        asyncio.run(source.search("Igatpuri", 40_000))
