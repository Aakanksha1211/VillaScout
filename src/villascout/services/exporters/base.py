from abc import ABC, abstractmethod
from pathlib import Path

from villascout.models.domain import Villa


class Exporter(ABC):
    @abstractmethod
    async def export(self, villas: list[Villa], output_path: Path) -> None:
        """Export villa records to a file."""
