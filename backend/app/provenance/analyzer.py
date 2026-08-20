"""Provenance Analyzer Facade."""

from app.models.schemas import CodeInput
from app.provenance.models import ProvenanceReport
from app.provenance.provenance_service import ProvenanceService


class ProvenanceAnalyzer:
    """Entrypoint for executing static provenance inspection."""

    @classmethod
    def analyze(cls, input_data: CodeInput) -> ProvenanceReport:
        return ProvenanceService.analyze_provenance(input_data)
