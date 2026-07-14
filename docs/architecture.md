# Architecture

VillaScout is organized as a small data platform rather than a one-off scraper.

## Layers

- **Discovery sources** implement `DiscoverySource` and return normalized `Villa` models.
- **Enrichment services** collect website HTML with Playwright and extract structured fields.
- **Persistence** stores normalized records through SQLAlchemy repositories.
- **Exporters** serialize canonical villa records to CSV, Excel, or JSON.
- **Pipeline orchestration** composes the services and isolates failures per source and listing.

## Adding A Source

Create a class under `src/villascout/services/discovery/` that implements:

```python
async def search(self, location: str, radius: int) -> list[Villa]:
    ...
```

Register it in the CLI composition root or in a future dependency container. No changes are required
to the database, exporters, or enrichment services as long as the source returns domain `Villa` models.
