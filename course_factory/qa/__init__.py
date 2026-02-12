"""Stage 6: Quality assurance - review and validate course content."""

from course_factory.pipeline.stage import Stage


class QAStage(Stage):
    """Run quality-assurance checks on generated media and content."""

    @property
    def name(self) -> str:
        return "qa"

    async def execute(self, context: dict) -> dict:
        raise NotImplementedError("QA stage not yet implemented")

    async def validate(self, context: dict) -> bool:
        return "media_assets" in context
