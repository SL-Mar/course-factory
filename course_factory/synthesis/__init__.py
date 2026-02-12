"""Stage 3: Course outline synthesis - structure the curriculum."""

from course_factory.pipeline.stage import Stage


class SynthesisStage(Stage):
    """Synthesize research data into a structured course outline."""

    @property
    def name(self) -> str:
        return "synthesis"

    async def execute(self, context: dict) -> dict:
        raise NotImplementedError("Synthesis stage not yet implemented")

    async def validate(self, context: dict) -> bool:
        return "research_data" in context
