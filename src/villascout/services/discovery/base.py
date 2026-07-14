from abc import ABC, abstractmethod

from villascout.models.domain import Villa


class DiscoverySource(ABC):
    name: str

    @abstractmethod
    async def search(self, location: str, radius: int) -> list[Villa]:
        """Search for villas/farmhouses around a location."""
