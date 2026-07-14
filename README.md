# VillaScout

VillaScout is an extensible villa and farmhouse discovery platform. It discovers accommodation
listings from source plugins, normalizes them into a shared schema, enriches listings from their
websites, stores them in a database, and exports clean datasets.

## Features

- Plugin-style discovery architecture.
- Google Places Nearby Search, Text Search, and Place Details integration.
- Website enrichment with Playwright and BeautifulSoup.
- Normalized SQLAlchemy persistence for SQLite, with PostgreSQL-ready configuration.
- CSV, Excel, and JSON exports.
- Structured JSON logging, retries, cache expiration, and per-listing failure isolation.
- Pytest coverage for discovery, parsing, exporters, and database persistence.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env
```

Set `GOOGLE_API_KEY` in `.env`.

## Configuration

Environment variables:

- `GOOGLE_API_KEY`: Google Places API key.
- `DATABASE_URL`: SQLAlchemy async database URL. Defaults to SQLite.
- `LOG_LEVEL`: Logging level such as `INFO` or `DEBUG`.
- `CACHE_DIRECTORY`: Directory for cached API responses and website HTML.
- `CACHE_TTL_SECONDS`: Cache freshness window.

## Running

```bash
python -m villascout \
  --location "Igatpuri" \
  --radius 40000 \
  --output output/villas.xlsx
```

Supported export extensions are `.csv`, `.xlsx`, and `.json`.

## Architecture

Discovery sources implement a common interface:

```python
class DiscoverySource:
    async def search(self, location: str, radius: int) -> list[Villa]:
        ...
```

The first implementation is `GooglePlacesSource`, which uses the official Google Places API. It
does not scrape Google Maps webpages. Future sources such as OpenStreetMap, StayVista, Booking,
Airbnb, and JustDial can be added by implementing the same interface and registering the source.

See [docs/architecture.md](docs/architecture.md) for extension notes.

## Database

The schema is normalized into:

- `villas`
- `contacts`
- `amenities`
- `prices`
- `source_listings`
- `review_summaries`

Google Place ID is stored as the external identifier in `source_listings`.

## Testing

```bash
pytest
ruff check .
ruff format --check .
```

## Docker

```bash
docker compose run --rm villascout
```

## Roadmap

- FastAPI service layer.
- Next.js dashboard.
- LLM-based review summarization.
- Image analysis and deduplication.
- Availability tracking.
- Price comparison across sources.
- Scheduling and notifications.
