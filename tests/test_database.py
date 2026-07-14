import asyncio
from pathlib import Path

import pytest

pytest.importorskip("aiosqlite")

from tests.factories import villa
from villascout.config import Settings
from villascout.database.repository import VillaRepository
from villascout.database.session import Database


def test_repository_upserts_by_source_listing(tmp_path: Path) -> None:
    async def run() -> None:
        settings = Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
        database = Database(settings)
        await database.create_schema()
        async with database.session() as session:
            repository = VillaRepository(session)
            await repository.upsert(villa("google-place-1"))
            updated = villa("google-place-1").model_copy(update={"name": "Casa Verde Estate"})
            await repository.upsert(updated)
            await session.commit()

            records = await repository.list_all()

        await database.engine.dispose()
        assert len(records) == 1
        assert records[0].name == "Casa Verde Estate"
        assert records[0].source_listing.external_id == "google-place-1"

    asyncio.run(run())
