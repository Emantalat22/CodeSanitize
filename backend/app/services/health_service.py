"""Health check and system status service."""

from app.config import get_settings
from app.models.schemas import HealthResponse, LanguageInfo
from app.parsers.registry import ParserRegistry


class HealthService:
    """Service providing application health status and language capability queries."""

    @staticmethod
    def get_health() -> HealthResponse:
        """Construct current system health response."""
        settings = get_settings()
        return HealthResponse(
            status="ok",
            app=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.ENVIRONMENT,
        )

    @staticmethod
    def get_supported_languages() -> list[LanguageInfo]:
        """Return list of supported languages and active parser readiness statuses."""
        return ParserRegistry.get_language_infos()
