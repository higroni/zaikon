"""Unit tests for procedure compliance service."""

from datetime import datetime
from uuid import uuid4

import pytest

from zaikon.modules.procedure.schemas import InstitutionalOpinion, ProcessArtifact
from zaikon.modules.procedure.service import ProcedureComplianceService


class TestProcedureComplianceService:
    """Tests for procedure compliance tracking."""

    def test_create_procedure_case(self):
        """Test creating a new procedure case."""
        service = ProcedureComplianceService()
        case = service.create_procedure_case(
            draft_title="Nacrt zakona o šumama",
            proposer="Ministarstvo poljoprivrede",
            procedure_type="government_bill",
            domain="forestry",
            eu_relevance="yes",
            budget_impact="no",
        )

        assert case.draft_title == "Nacrt zakona o šumama"
        assert case.proposer == "Ministarstvo poljoprivrede"
        assert case.procedure_type == "government_bill"
        assert case.current_stage == "drafting_and_ria"
        assert case.status == "in_progress"
        assert case.eu_relevance == "yes"
        assert case.budget_impact == "no"

    def test_add_artifact(self):
        """Test adding a procedural artifact."""
        service = ProcedureComplianceService()
        procedure_case_id = uuid4()

        artifact = service.add_artifact(
            procedure_case_id=procedure_case_id,
            artifact_type="rsz_opinion",
            title="Mišljenje RSZ",
            issuer="Republički sekretarijat za zakonodavstvo",
            status="positive",
        )

        assert artifact.procedure_case_id == procedure_case_id
        assert artifact.artifact_type == "rsz_opinion"
        assert artifact.title == "Mišljenje RSZ"
        assert artifact.issuer == "Republički sekretarijat za zakonodavstvo"
        assert artifact.status == "positive"

    def test_readiness_report_ready(self):
        """Test readiness report when all requirements are met."""
        service = ProcedureComplianceService()

        case = service.create_procedure_case(
            draft_title="Test Draft",
            procedure_type="government_bill",
            eu_relevance="no",
            budget_impact="no",
        )
        case.current_stage = "official_opinions"

        # Add required RSZ opinion
        artifacts = [
            ProcessArtifact(
                procedure_case_id=case.procedure_case_id,
                artifact_type="rsz_opinion",
                title="RSZ Opinion",
                status="positive",
            )
        ]

        report = service.generate_readiness_report(
            procedure_case=case, artifacts=artifacts, opinions=[]
        )

        assert report.readiness_status == "ready"
        assert len(report.missing_artifacts) == 0
        assert len(report.blocking_issues) == 0

    def test_readiness_report_missing_rsz_opinion(self):
        """Test readiness report when RSZ opinion is missing."""
        service = ProcedureComplianceService()

        case = service.create_procedure_case(
            draft_title="Test Draft",
            procedure_type="government_bill",
            eu_relevance="no",
            budget_impact="no",
        )
        case.current_stage = "official_opinions"

        report = service.generate_readiness_report(
            procedure_case=case, artifacts=[], opinions=[]
        )

        assert report.readiness_status == "blocked"
        assert "rsz_opinion" in report.missing_artifacts
        assert any("rsz_opinion" in issue.lower() for issue in report.blocking_issues)
        assert any(
            "rsz" in rec.lower() for rec in report.recommendations
        ), "Should recommend getting RSZ opinion"

    def test_readiness_report_eu_relevance_without_alignment(self):
        """Test blocking when EU relevance is yes but alignment statement missing."""
        service = ProcedureComplianceService()

        case = service.create_procedure_case(
            draft_title="Test Draft",
            procedure_type="government_bill",
            eu_relevance="yes",
            budget_impact="no",
        )
        case.current_stage = "eu_alignment_package"

        report = service.generate_readiness_report(
            procedure_case=case, artifacts=[], opinions=[]
        )

        assert report.readiness_status == "blocked"
        assert "eu_alignment_statement" in report.missing_artifacts
        assert any(
            "alignment" in issue.lower() for issue in report.blocking_issues
        ), "Should block on missing EU alignment"

    def test_readiness_report_unresolved_negative_opinion(self):
        """Test blocking when there's an unresolved negative opinion."""
        service = ProcedureComplianceService()

        case = service.create_procedure_case(
            draft_title="Test Draft",
            procedure_type="government_bill",
            eu_relevance="no",
            budget_impact="no",
        )
        case.current_stage = "official_opinions"

        # Add RSZ opinion but with negative status and unresolved remarks
        artifacts = [
            ProcessArtifact(
                procedure_case_id=case.procedure_case_id,
                artifact_type="rsz_opinion",
                title="RSZ Opinion",
                status="negative",
            )
        ]

        opinions = [
            InstitutionalOpinion(
                procedure_case_id=case.procedure_case_id,
                institution="RSZ",
                opinion_status="negative",
                summary="Negative opinion with unresolved issues",
                open_remarks=[
                    {
                        "remark_id": str(uuid4()),
                        "target_path": "article:5",
                        "content_text": "This article conflicts with Constitution",
                        "resolved": False,
                    }
                ],
            )
        ]

        report = service.generate_readiness_report(
            procedure_case=case, artifacts=artifacts, opinions=opinions
        )

        assert report.readiness_status == "blocked"
        assert len(report.unresolved_opinions) > 0
        assert any(
            "negative" in issue.lower() for issue in report.blocking_issues
        ), "Should block on negative opinion"

    def test_readiness_report_warnings(self):
        """Test that warnings are generated for unknown statuses."""
        service = ProcedureComplianceService()

        case = service.create_procedure_case(
            draft_title="Test Draft",
            procedure_type="government_bill",
            eu_relevance="unknown",
            budget_impact="unknown",
        )

        report = service.generate_readiness_report(
            procedure_case=case, artifacts=[], opinions=[]
        )

        assert any(
            "budget" in warning.lower() for warning in report.warnings
        ), "Should warn about unknown budget impact"
        assert any(
            "eu" in warning.lower() for warning in report.warnings
        ), "Should warn about unknown EU relevance"

    def test_next_stage_progression(self):
        """Test that next stage is correctly determined."""
        service = ProcedureComplianceService()

        case = service.create_procedure_case(
            draft_title="Test Draft", procedure_type="government_bill"
        )

        # Test progression through stages
        assert service._next_stage("drafting_and_ria") == "public_consultation"
        assert service._next_stage("public_consultation") == "official_opinions"
        assert service._next_stage("official_opinions") == "eu_alignment_package"
        assert (
            service._next_stage("eu_alignment_package") == "government_committees"
        )
        assert service._next_stage("government_committees") == "government_adoption"
        assert service._next_stage("government_adoption") == "parliamentary_review"
        assert service._next_stage("parliamentary_review") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
