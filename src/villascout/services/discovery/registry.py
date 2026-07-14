from villascout.services.discovery.base import DiscoverySource


class DiscoveryRegistry:
    def __init__(self) -> None:
        self._sources: dict[str, DiscoverySource] = {}

    def register(self, source: DiscoverySource) -> None:
        self._sources[source.name] = source

    def all(self) -> list[DiscoverySource]:
        return list(self._sources.values())
