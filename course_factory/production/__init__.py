"""Stage 4: Content production - generate scripts and slides."""

from course_factory.pipeline.stage import Stage


class ProductionStage(Stage):
    """Produce lesson scripts, slide decks, and supporting materials."""

    @property
    def name(self) -> str:
        return "production"

    async def execute(self, context: dict) -> dict:
        raise NotImplementedError("Production stage not yet implemented")

    async def validate(self, context: dict) -> bool:
        return "outline" in context
