import json
from asyncio import to_thread
from pathlib import Path
from typing import Any

import pandas as pd

from villascout.models.domain import Villa
from villascout.services.exporters.base import Exporter


class VillaSerializer:
    def to_rows(self, villas: list[Villa]) -> list[dict[str, Any]]:
        return [self.to_row(villa) for villa in villas]

    def to_row(self, villa: Villa) -> dict[str, Any]:
        return {
            "name": villa.name,
            "location": villa.location,
            "address": villa.address,
            "latitude": villa.latitude,
            "longitude": villa.longitude,
            "website": str(villa.contact.website) if villa.contact.website else None,
            "phone": villa.contact.phone,
            "email": villa.contact.email,
            "whatsapp": villa.contact.whatsapp,
            "instagram": villa.contact.instagram,
            "bedrooms": villa.amenities.bedrooms,
            "bathrooms": villa.amenities.bathrooms,
            "guests": villa.amenities.guests,
            "pool": villa.amenities.pool,
            "private_pool": villa.amenities.private_pool,
            "bbq": villa.amenities.bbq,
            "bonfire": villa.amenities.bonfire,
            "parking": villa.amenities.parking,
            "wifi": villa.amenities.wifi,
            "pet_friendly": villa.amenities.pet_friendly,
            "caretaker": villa.amenities.caretaker,
            "check_in": villa.amenities.check_in,
            "check_out": villa.amenities.check_out,
            "price_amount": villa.price.amount,
            "price_currency": villa.price.currency,
            "price_unit": villa.price.unit,
            "price_raw_text": villa.price.raw_text,
            "rating": villa.review_summary.rating,
            "review_count": villa.review_summary.review_count,
            "source": villa.source_listing.source.value,
            "external_id": villa.source_listing.external_id,
            "source_url": villa.source_listing.source_url,
            "categories": ", ".join(villa.categories),
            "images": ", ".join(villa.images),
            "enriched_at": villa.enriched_at.isoformat() if villa.enriched_at else None,
        }


class CsvExporter(Exporter):
    def __init__(self, serializer: VillaSerializer | None = None) -> None:
        self.serializer = serializer or VillaSerializer()

    async def export(self, villas: list[Villa], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.serializer.to_rows(villas)).to_csv(output_path, index=False)


class ExcelExporter(Exporter):
    def __init__(self, serializer: VillaSerializer | None = None) -> None:
        self.serializer = serializer or VillaSerializer()

    async def export(self, villas: list[Villa], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.serializer.to_rows(villas)).to_excel(output_path, index=False)


class JsonExporter(Exporter):
    async def export(self, villas: list[Villa], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [villa.model_dump(mode="json") for villa in villas]
        await to_thread(
            output_path.write_text,
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class ExporterFactory:
    def create(self, output_path: Path) -> Exporter:
        suffix = output_path.suffix.lower()
        if suffix == ".csv":
            return CsvExporter()
        if suffix in {".xlsx", ".xls"}:
            return ExcelExporter()
        if suffix == ".json":
            return JsonExporter()
        raise ValueError(f"Unsupported export format: {suffix}")
