"""Stage 2: Deep research - retrieve and synthesize source material."""

from course_factory.pipeline.stage import Stage


class ResearchStage(Stage):
    """Perform deep research on discovered sources."""

    @property
    def name(self) -> str:
        return "research"

    async def execute(self, context: dict) -> dict:
        raise NotImplementedError("Research stage not yet implemented")

    async def validate(self, context: dict) -> bool:
        return "sources" in context
