from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceName(StrEnum):
    GOOGLE_PLACES = "google_places"


class Contact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str | None = None
    email: str | None = None
    website: HttpUrl | None = None
    whatsapp: str | None = None
    instagram: str | None = None


class AmenitySet(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bedrooms: int | None = None
    bathrooms: int | None = None
    guests: int | None = None
    pool: bool | None = None
    private_pool: bool | None = None
    bbq: bool | None = None
    bonfire: bool | None = None
    parking: bool | None = None
    wifi: bool | None = None
    pet_friendly: bool | None = None
    caretaker: bool | None = None
    check_in: str | None = None
    check_out: str | None = None


class Price(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: float | None = None
    currency: str = "INR"
    unit: str | None = None
    raw_text: str | None = None


class ReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: float | None = None
    review_count: int | None = None
    summary: str | None = None


class SourceListing(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourceName
    external_id: str
    source_url: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Villa(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    location: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    contact: Contact = Field(default_factory=Contact)
    amenities: AmenitySet = Field(default_factory=AmenitySet)
    price: Price = Field(default_factory=Price)
    review_summary: ReviewSummary = Field(default_factory=ReviewSummary)
    source_listing: SourceListing
    images: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    enriched_at: datetime | None = None
