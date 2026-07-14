import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from villascout.utils.logging import get_logger


class FileCache:
    def __init__(self, directory: Path, ttl_seconds: int) -> None:
        self.directory = directory
        self.ttl = timedelta(seconds=ttl_seconds)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("cache")

    async def get_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        path = self._path(namespace, key, ".json")
        if not path.exists() or self._expired(path):
            return None
        self.logger.info("cache_hit", namespace=namespace, key=key)
        return json.loads(path.read_text(encoding="utf-8"))

    async def set_json(self, namespace: str, key: str, value: dict[str, Any]) -> None:
        path = self._path(namespace, key, ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    async def get_text(self, namespace: str, key: str) -> str | None:
        path = self._path(namespace, key, ".html")
        if not path.exists() or self._expired(path):
            return None
        self.logger.info("cache_hit", namespace=namespace, key=key)
        return path.read_text(encoding="utf-8")

    async def set_text(self, namespace: str, key: str, value: str) -> None:
        path = self._path(namespace, key, ".html")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def _path(self, namespace: str, key: str, suffix: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.directory / namespace / f"{digest}{suffix}"

    def _expired(self, path: Path) -> bool:
        modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        return datetime.now(UTC) - modified_at > self.ttl
