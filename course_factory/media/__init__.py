"""Stage 5: Media generation - TTS audio and video rendering."""

from course_factory.pipeline.stage import Stage


class MediaStage(Stage):
    """Generate audio (TTS) and video assets from production scripts."""

    @property
    def name(self) -> str:
        return "media"

    async def execute(self, context: dict) -> dict:
        raise NotImplementedError("Media stage not yet implemented")

    async def validate(self, context: dict) -> bool:
        return "scripts" in context
