"""Stage 1: Source discovery - find and catalog knowledge sources."""

from course_factory.pipeline.stage import Stage


class DiscoveryStage(Stage):
    """Discover and catalog external knowledge sources (URLs, papers, repos)."""

    @property
    def name(self) -> str:
        return "discovery"

    async def execute(self, context: dict) -> dict:
        raise NotImplementedError("Discovery stage not yet implemented")

    async def validate(self, context: dict) -> bool:
        return "source_urls" in context
