"""Procedure compliance service for legislative workflow tracking."""

from datetime import datetime
from pathlib import Path
from uuid import UUID

from zaikon.core.config import settings
from zaikon.modules.procedure.schemas import (
    InstitutionalOpinion,
    ProcedureCase,
    ProcessArtifact,
    ProcessRequirement,
    ReadinessReport,
)


class ProcedureComplianceService:
    """
    Tracks draft through legislative procedure stages.
    Checks for missing artifacts, unresolved opinions, and readiness gates.
    """

    def __init__(self, rules_dir: Path | None = None) -> None:
        self.rules_dir = rules_dir or (
            settings.base_dir / "backend" / "zaikon" / "rules" / "procedure"
        )
        self._requirements: list[ProcessRequirement] = []
        self._load_requirements()

    def create_procedure_case(
        self,
        *,
        draft_review_id: UUID | None = None,
        draft_title: str,
        proposer: str | None = None,
        procedure_type: str = "government_bill",
        domain: str | None = None,
        eu_relevance: str = "unknown",
        budget_impact: str = "unknown",
    ) -> ProcedureCase:
        """Create a new procedure case for tracking."""
        return ProcedureCase(
            draft_review_id=draft_review_id,
            draft_title=draft_title,
            proposer=proposer,
            procedure_type=procedure_type,  # type: ignore
            domain=domain,
            eu_relevance=eu_relevance,  # type: ignore
            budget_impact=budget_impact,  # type: ignore
            current_stage="drafting_and_ria",
            status="in_progress",
        )

    def add_artifact(
        self,
        *,
        procedure_case_id: UUID,
        artifact_type: str,
        title: str,
        source_uri: str | None = None,
        issuer: str | None = None,
        issued_at: datetime | None = None,
        status: str = "submitted",
        content_text: str | None = None,
    ) -> ProcessArtifact:
        """Add a procedural artifact (RIA, opinion, alignment table, etc.)."""
        return ProcessArtifact(
            procedure_case_id=procedure_case_id,
            artifact_type=artifact_type,  # type: ignore
            title=title,
            source_uri=source_uri,
            issuer=issuer,
            issued_at=issued_at,
            status=status,  # type: ignore
            content_text=content_text,
        )

    def generate_readiness_report(
        self,
        *,
        procedure_case: ProcedureCase,
        artifacts: list[ProcessArtifact],
        opinions: list[InstitutionalOpinion],
    ) -> ReadinessReport:
        """
        Generate readiness report for current stage.
        Checks what's missing and what blocks progression.
        """
        missing_artifacts = self._check_missing_artifacts(
            procedure_case=procedure_case, artifacts=artifacts
        )
        unresolved_opinions = self._check_unresolved_opinions(opinions=opinions)
        blocking_issues = self._check_blocking_issues(
            procedure_case=procedure_case,
            missing_artifacts=missing_artifacts,
            unresolved_opinions=unresolved_opinions,
        )

        if blocking_issues:
            readiness_status = "blocked"
        elif missing_artifacts or unresolved_opinions:
            readiness_status = "incomplete"
        else:
            readiness_status = "ready"

        next_stage = self._next_stage(procedure_case.current_stage)

        return ReadinessReport(
            procedure_case_id=procedure_case.procedure_case_id,
            current_stage=procedure_case.current_stage,
            next_stage=next_stage,
            readiness_status=readiness_status,  # type: ignore
            missing_artifacts=missing_artifacts,
            unresolved_opinions=unresolved_opinions,
            blocking_issues=blocking_issues,
            warnings=self._generate_warnings(
                procedure_case=procedure_case, artifacts=artifacts
            ),
            recommendations=self._generate_recommendations(
                missing_artifacts=missing_artifacts,
                unresolved_opinions=unresolved_opinions,
            ),
        )

    def _check_missing_artifacts(
        self, *, procedure_case: ProcedureCase, artifacts: list[ProcessArtifact]
    ) -> list[str]:
        """Check which required artifacts are missing for current stage."""
        missing = []
        required = self._get_required_artifacts(
            procedure_type=procedure_case.procedure_type,
            stage=procedure_case.current_stage,
            eu_relevance=procedure_case.eu_relevance,
            budget_impact=procedure_case.budget_impact,
        )

        artifact_types = {artifact.artifact_type for artifact in artifacts}

        for req in required:
            if req.required_artifact_type not in artifact_types:
                missing.append(req.required_artifact_type)

        return missing

    def _check_unresolved_opinions(
        self, *, opinions: list[InstitutionalOpinion]
    ) -> list[str]:
        """Check which institutional opinions have unresolved remarks."""
        unresolved = []
        for opinion in opinions:
            if opinion.opinion_status in ["negative", "conditional"]:
                open_count = sum(
                    1 for remark in opinion.open_remarks if not remark.get("resolved")
                )
                if open_count > 0:
                    unresolved.append(
                        f"{opinion.institution}: {open_count} unresolved remarks (status: {opinion.opinion_status})"
                    )
        return unresolved

    def _check_blocking_issues(
        self,
        *,
        procedure_case: ProcedureCase,
        missing_artifacts: list[str],
        unresolved_opinions: list[str],
    ) -> list[str]:
        """Identify issues that block progression to next stage."""
        blocking = []

        # High-severity missing artifacts block progression
        high_severity_artifacts = {"rsz_opinion", "finance_opinion", "ria"}
        for artifact in missing_artifacts:
            if artifact in high_severity_artifacts:
                blocking.append(f"Missing required artifact: {artifact}")

        # Negative opinions block progression
        for opinion_str in unresolved_opinions:
            if "negative" in opinion_str.lower():
                blocking.append(f"Unresolved negative institutional opinion: {opinion_str}")

        # EU relevance without alignment package blocks
        if (
            procedure_case.eu_relevance == "yes"
            and "eu_alignment_statement" in missing_artifacts
        ):
            blocking.append("EU relevance declared but alignment statement missing")

        return blocking

    def _generate_warnings(
        self, *, procedure_case: ProcedureCase, artifacts: list[ProcessArtifact]
    ) -> list[str]:
        """Generate non-blocking warnings."""
        warnings = []

        if procedure_case.budget_impact == "unknown":
            warnings.append("Budget impact not assessed")

        if procedure_case.eu_relevance == "unknown":
            warnings.append("EU relevance not determined")

        # Check for conditional opinions
        for artifact in artifacts:
            if artifact.status == "conditional":
                warnings.append(
                    f"Conditional opinion from {artifact.issuer or 'unknown'}"
                )

        return warnings

    def _generate_recommendations(
        self, *, missing_artifacts: list[str], unresolved_opinions: list[str]
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if "ria" in missing_artifacts:
            recommendations.append(
                "Prepare Regulatory Impact Assessment (RIA) or mark as not required"
            )

        if "rsz_opinion" in missing_artifacts:
            recommendations.append(
                "Request opinion from Republican Secretariat for Legislation (RSZ)"
            )

        if "finance_opinion" in missing_artifacts:
            recommendations.append("Request opinion from Ministry of Finance")

        if unresolved_opinions:
            recommendations.append(
                "Address unresolved remarks from institutional opinions"
            )

        if "eu_alignment_statement" in missing_artifacts:
            recommendations.append("Prepare EU alignment statement and table")

        return recommendations

    def _get_required_artifacts(
        self,
        *,
        procedure_type: str,
        stage: str,
        eu_relevance: str,
        budget_impact: str,
    ) -> list[ProcessRequirement]:
        """Get required artifacts for given procedure context."""
        required = []
        for req in self._requirements:
            if req.procedure_type != procedure_type:
                continue
            if req.stage != stage:
                continue

            # Check conditional requirements
            when = req.required_when
            if when.get("eu_relevance") and eu_relevance != when["eu_relevance"]:
                continue
            if when.get("budget_impact") and budget_impact != when["budget_impact"]:
                continue

            required.append(req)

        return required

    def _next_stage(self, current_stage: str) -> str | None:
        """Determine next stage in procedure."""
        stage_order = [
            "drafting_and_ria",
            "public_consultation",
            "official_opinions",
            "eu_alignment_package",
            "government_committees",
            "government_adoption",
            "parliamentary_review",
        ]
        try:
            current_index = stage_order.index(current_stage)
            if current_index < len(stage_order) - 1:
                return stage_order[current_index + 1]
        except ValueError:
            pass
        return None

    def _load_requirements(self) -> None:
        """Load process requirements from rule files."""
        # MVP: hardcoded requirements
        # TODO: Load from YAML/JSON files
        self._requirements = [
            ProcessRequirement(
                procedure_type="government_bill",
                stage="official_opinions",
                required_artifact_type="rsz_opinion",
                required_when={"document_type": "law"},
                severity_if_missing="high",
            ),
            ProcessRequirement(
                procedure_type="government_bill",
                stage="official_opinions",
                required_artifact_type="finance_opinion",
                required_when={"budget_impact": "yes"},
                severity_if_missing="high",
            ),
            ProcessRequirement(
                procedure_type="government_bill",
                stage="eu_alignment_package",
                required_artifact_type="eu_alignment_statement",
                required_when={"eu_relevance": "yes"},
                severity_if_missing="high",
            ),
            ProcessRequirement(
                procedure_type="government_bill",
                stage="public_consultation",
                required_artifact_type="public_debate_report",
                required_when={},
                severity_if_missing="medium",
            ),
        ]

# Made with Bob
