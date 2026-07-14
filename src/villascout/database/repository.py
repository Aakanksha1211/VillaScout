from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from villascout.database.models import (
    AmenityRecord,
    ContactRecord,
    PriceRecord,
    ReviewSummaryRecord,
    SourceListingRecord,
    VillaRecord,
)
from villascout.models.domain import AmenitySet, Contact, Price, ReviewSummary, SourceListing, Villa


class VillaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, villa: Villa) -> VillaRecord:
        existing = await self._find_by_source_listing(villa.source_listing)
        record = existing or VillaRecord(name=villa.name)
        record.name = villa.name
        record.location = villa.location
        record.address = villa.address
        record.latitude = villa.latitude
        record.longitude = villa.longitude
        record.description = villa.description
        record.categories = villa.categories
        record.images = villa.images
        record.enriched_at = villa.enriched_at

        if record.contact is None:
            record.contact = ContactRecord()
        record.contact.phone = villa.contact.phone
        record.contact.email = villa.contact.email
        record.contact.website = str(villa.contact.website) if villa.contact.website else None
        record.contact.whatsapp = villa.contact.whatsapp
        record.contact.instagram = villa.contact.instagram

        record.amenities.clear()
        record.amenities.extend(
            AmenityRecord(name=name, value=str(value))
            for name, value in villa.amenities.model_dump().items()
            if value is not None
        )

        if not record.prices:
            record.prices.append(PriceRecord())
        price_record = record.prices[0]
        price_record.amount = villa.price.amount
        price_record.currency = villa.price.currency
        price_record.unit = villa.price.unit
        price_record.raw_text = villa.price.raw_text

        if record.review_summary is None:
            record.review_summary = ReviewSummaryRecord()
        record.review_summary.rating = villa.review_summary.rating
        record.review_summary.review_count = villa.review_summary.review_count
        record.review_summary.summary = villa.review_summary.summary

        if existing is None:
            record.source_listings = [
                SourceListingRecord(
                    source=villa.source_listing.source.value,
                    external_id=villa.source_listing.external_id,
                    source_url=villa.source_listing.source_url,
                    raw_payload=villa.source_listing.raw_payload,
                    discovered_at=villa.source_listing.discovered_at,
                )
            ]
            self.session.add(record)
        else:
            listing = record.source_listings[0]
            listing.source_url = villa.source_listing.source_url
            listing.raw_payload = villa.source_listing.raw_payload
            listing.discovered_at = villa.source_listing.discovered_at

        await self.session.flush()
        return record

    async def list_all(self) -> list[Villa]:
        result = await self.session.execute(
            select(VillaRecord).options(
                selectinload(VillaRecord.contact),
                selectinload(VillaRecord.amenities),
                selectinload(VillaRecord.prices),
                selectinload(VillaRecord.source_listings),
                selectinload(VillaRecord.review_summary),
            )
        )
        return [self._to_domain(record) for record in result.scalars().all()]

    async def _find_by_source_listing(self, source_listing: SourceListing) -> VillaRecord | None:
        result = await self.session.execute(
            select(VillaRecord)
            .join(SourceListingRecord)
            .options(
                selectinload(VillaRecord.contact),
                selectinload(VillaRecord.amenities),
                selectinload(VillaRecord.prices),
                selectinload(VillaRecord.source_listings),
                selectinload(VillaRecord.review_summary),
            )
            .where(
                SourceListingRecord.source == source_listing.source.value,
                SourceListingRecord.external_id == source_listing.external_id,
            )
        )
        return result.scalars().first()

    def _to_domain(self, record: VillaRecord) -> Villa:
        amenities = {
            amenity.name: self._coerce_value(amenity.value) for amenity in record.amenities
        }
        price = record.prices[0] if record.prices else None
        source_listing = record.source_listings[0]
        return Villa(
            name=record.name,
            location=record.location,
            address=record.address,
            latitude=record.latitude,
            longitude=record.longitude,
            description=record.description,
            contact=Contact(
                phone=record.contact.phone if record.contact else None,
                email=record.contact.email if record.contact else None,
                website=record.contact.website if record.contact else None,
                whatsapp=record.contact.whatsapp if record.contact else None,
                instagram=record.contact.instagram if record.contact else None,
            ),
            amenities=AmenitySet(**amenities),
            price=Price(
                amount=price.amount if price else None,
                currency=price.currency if price else "INR",
                unit=price.unit if price else None,
                raw_text=price.raw_text if price else None,
            ),
            review_summary=ReviewSummary(
                rating=record.review_summary.rating if record.review_summary else None,
                review_count=record.review_summary.review_count if record.review_summary else None,
                summary=record.review_summary.summary if record.review_summary else None,
            ),
            source_listing=SourceListing(
                source=source_listing.source,
                external_id=source_listing.external_id,
                source_url=source_listing.source_url,
                raw_payload=source_listing.raw_payload,
                discovered_at=source_listing.discovered_at,
            ),
            images=record.images or [],
            categories=record.categories or [],
            enriched_at=record.enriched_at,
        )

    @staticmethod
    def _coerce_value(value: str | None) -> str | int | bool | None:
        if value is None:
            return None
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if value.isdigit():
            return int(value)
        return value
