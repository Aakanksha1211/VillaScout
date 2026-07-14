from collections.abc import Iterable
from hashlib import sha256
from typing import Any

from villascout.config import Settings
from villascout.models.domain import (
    Contact,
    ReviewSummary,
    SourceListing,
    SourceName,
    Villa,
)
from villascout.services.discovery.base import DiscoverySource
from villascout.utils.cache import FileCache
from villascout.utils.http import HttpClient
from villascout.utils.logging import get_logger


class GooglePlacesError(RuntimeError):
    pass


class GooglePlacesSource(DiscoverySource):
    name = SourceName.GOOGLE_PLACES.value
    _base_url = "https://maps.googleapis.com/maps/api/place"

    def __init__(
        self,
        settings: Settings,
        http_client: HttpClient,
        cache: FileCache,
        keywords: Iterable[str] | None = None,
    ) -> None:
        self.settings = settings
        self.http_client = http_client
        self.cache = cache
        self.keywords = list(
            keywords
            or [
                "villa",
                "farmhouse",
                "homestay",
                "pool villa",
                "holiday home",
                "resort",
                "bungalow",
            ]
        )
        self.logger = get_logger("discovery.google_places")

    async def search(self, location: str, radius: int) -> list[Villa]:
        if not self.settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for Google Places discovery.")

        villas: dict[str, Villa] = {}
        for keyword in self.keywords:
            for result in await self._text_search(location, keyword):
                villa = await self._build_villa(result, location)
                villas[villa.source_listing.external_id] = villa

            coordinates = await self._geocode(location)
            if coordinates is not None:
                for result in await self._nearby_search(coordinates, radius, keyword):
                    villa = await self._build_villa(result, location)
                    villas[villa.source_listing.external_id] = villa

        self.logger.info("discovery_complete", count=len(villas), source=self.name)
        return list(villas.values())

    async def _text_search(self, location: str, keyword: str) -> list[dict[str, Any]]:
        query = f"{keyword} in {location}"
        return await self._paged_request("textsearch/json", {"query": query})

    async def _nearby_search(
        self, coordinates: tuple[float, float], radius: int, keyword: str
    ) -> list[dict[str, Any]]:
        lat, lng = coordinates
        return await self._paged_request(
            "nearbysearch/json",
            {"location": f"{lat},{lng}", "radius": radius, "keyword": keyword},
        )

    async def _build_villa(self, result: dict[str, Any], location: str) -> Villa:
        place_id = result["place_id"]
        details = await self._place_details(place_id)
        geometry = details.get("geometry", {}).get("location", {})
        website = details.get("website")
        return Villa(
            name=details.get("name") or result.get("name", "Unknown property"),
            location=location,
            address=details.get("formatted_address") or result.get("vicinity"),
            latitude=geometry.get("lat"),
            longitude=geometry.get("lng"),
            contact=Contact(
                phone=details.get("formatted_phone_number")
                or details.get("international_phone_number"),
                website=website,
            ),
            review_summary=ReviewSummary(
                rating=details.get("rating"),
                review_count=details.get("user_ratings_total"),
            ),
            source_listing=SourceListing(
                source=SourceName.GOOGLE_PLACES,
                external_id=place_id,
                source_url=details.get("url"),
                raw_payload=details,
            ),
            images=self._photo_urls(details),
            categories=details.get("types", []),
        )

    async def _place_details(self, place_id: str) -> dict[str, Any]:
        fields = ",".join(
            [
                "place_id",
                "name",
                "formatted_address",
                "formatted_phone_number",
                "international_phone_number",
                "website",
                "url",
                "geometry",
                "rating",
                "user_ratings_total",
                "types",
                "photos",
            ]
        )
        payload = await self._cached_request(
            "details/json", {"place_id": place_id, "fields": fields}, cache_key=place_id
        )
        return payload.get("result", {})

    async def _geocode(self, location: str) -> tuple[float, float] | None:
        payload = await self._cached_request(
            "findplacefromtext/json",
            {
                "input": location,
                "inputtype": "textquery",
                "fields": "geometry",
            },
            cache_key=f"geocode:{location}",
        )
        candidates = payload.get("candidates", [])
        if not candidates:
            return None
        point = candidates[0].get("geometry", {}).get("location", {})
        if "lat" not in point or "lng" not in point:
            return None
        return float(point["lat"]), float(point["lng"])

    async def _paged_request(self, endpoint: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        payload = await self._cached_request(endpoint, params, cache_key=f"{endpoint}:{params}")
        results = list(payload.get("results", []))
        next_page_token = payload.get("next_page_token")
        if next_page_token:
            next_payload = await self._cached_request(
                endpoint,
                {"pagetoken": next_page_token},
                cache_key=f"{endpoint}:page:{next_page_token}",
            )
            results.extend(next_payload.get("results", []))
        return results

    async def _cached_request(
        self, endpoint: str, params: dict[str, Any], *, cache_key: str
    ) -> dict[str, Any]:
        key = f"{endpoint}:{self._api_key_fingerprint()}:{cache_key}"
        cached = await self.cache.get_json("google_places", key)
        if cached is not None:
            return cached
        payload = await self.http_client.get_json(
            f"{self._base_url}/{endpoint}",
            params={**params, "key": self.settings.google_api_key},
        )
        status = payload.get("status")
        if status not in {"OK", "ZERO_RESULTS"}:
            message = payload.get("error_message")
            self.logger.warning(
                "google_places_non_ok_status",
                status=status,
                endpoint=endpoint,
                message=message,
            )
            if status == "REQUEST_DENIED":
                raise GooglePlacesError(
                    "Google Places request was denied. Check that billing is enabled, "
                    "Places API is enabled, and API key restrictions allow this API."
                )
            return payload
        await self.cache.set_json("google_places", key, payload)
        return payload

    def _photo_urls(self, details: dict[str, Any]) -> list[str]:
        return [
            f"{self._base_url}/photo?maxwidth=1200&photo_reference={photo['photo_reference']}&key={self.settings.google_api_key}"
            for photo in details.get("photos", [])
            if "photo_reference" in photo
        ]

    def _api_key_fingerprint(self) -> str:
        return sha256(self.settings.google_api_key.encode("utf-8")).hexdigest()[:12]
