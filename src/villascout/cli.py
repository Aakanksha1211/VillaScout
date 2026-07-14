import argparse
import asyncio
from pathlib import Path

from villascout.config import get_settings
from villascout.database.session import Database
from villascout.services.discovery.google_places import GooglePlacesSource
from villascout.services.discovery.registry import DiscoveryRegistry
from villascout.services.enrichment.website import WebsiteEnricher
from villascout.services.exporters.tabular import ExporterFactory
from villascout.services.pipeline import CrawlPipeline
from villascout.utils.cache import FileCache
from villascout.utils.http import HttpClient
from villascout.utils.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="villascout",
        description="Discover, enrich, store, and export villa/farmhouse listings.",
    )
    parser.add_argument("--location", required=True, help="Location or region to search.")
    parser.add_argument("--radius", type=int, default=40_000, help="Search radius in meters.")
    parser.add_argument("--output", required=True, help="Output file path: .csv, .xlsx, or .json.")
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=None,
        help="Optional Google Places search keywords.",
    )
    return parser


async def run_async(args: argparse.Namespace) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    cache = FileCache(settings.cache_directory, settings.cache_ttl_seconds)
    http_client = HttpClient(settings)
    database = Database(settings)
    try:
        registry = DiscoveryRegistry()
        registry.register(
            GooglePlacesSource(
                settings,
                http_client=http_client,
                cache=cache,
                keywords=args.keywords,
            )
        )
        pipeline = CrawlPipeline(
            database=database,
            discovery_registry=registry,
            enricher=WebsiteEnricher(cache),
            exporter_factory=ExporterFactory(),
        )
        await pipeline.run(args.location, args.radius, Path(args.output))
    finally:
        await http_client.close()
        await database.engine.dispose()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run_async(args))
