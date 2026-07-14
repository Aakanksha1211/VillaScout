import asyncio
from pathlib import Path

from villascout.database.repository import VillaRepository
from villascout.database.session import Database
from villascout.models.domain import Villa
from villascout.services.discovery.registry import DiscoveryRegistry
from villascout.services.enrichment.website import WebsiteEnricher
from villascout.services.exporters.tabular import ExporterFactory
from villascout.utils.logging import get_logger


class CrawlPipeline:
    def __init__(
        self,
        database: Database,
        discovery_registry: DiscoveryRegistry,
        enricher: WebsiteEnricher,
        exporter_factory: ExporterFactory,
    ) -> None:
        self.database = database
        self.discovery_registry = discovery_registry
        self.enricher = enricher
        self.exporter_factory = exporter_factory
        self.logger = get_logger("pipeline")

    async def run(self, location: str, radius: int, output_path: Path) -> list[Villa]:
        await self.database.create_schema()
        discovered = await self._discover(location, radius)
        enriched = await self._enrich(discovered)
        async with self.database.session() as session:
            repository = VillaRepository(session)
            for villa in enriched:
                try:
                    await repository.upsert(villa)
                except Exception as exc:
                    self.logger.warning(
                        "villa_persistence_failed",
                        villa=villa.name,
                        external_id=villa.source_listing.external_id,
                        error=str(exc),
                    )
            await session.commit()
            villas = await repository.list_all()
        exporter = self.exporter_factory.create(output_path)
        await exporter.export(villas, output_path)
        self.logger.info("pipeline_complete", exported=len(villas), output=str(output_path))
        return villas

    async def _discover(self, location: str, radius: int) -> list[Villa]:
        villas: dict[str, Villa] = {}
        for source in self.discovery_registry.all():
            try:
                for villa in await source.search(location, radius):
                    villas[villa.source_listing.external_id] = villa
            except Exception as exc:
                self.logger.warning("discovery_source_failed", source=source.name, error=str(exc))
        return list(villas.values())

    async def _enrich(self, villas: list[Villa]) -> list[Villa]:
        tasks = [self.enricher.enrich(villa) for villa in villas]
        enriched = await asyncio.gather(*tasks, return_exceptions=True)
        results: list[Villa] = []
        for original, result in zip(villas, enriched, strict=True):
            if isinstance(result, Exception):
                self.logger.warning(
                    "villa_enrichment_failed",
                    villa=original.name,
                    error=str(result),
                )
                results.append(original)
            else:
                results.append(result)
        return results
