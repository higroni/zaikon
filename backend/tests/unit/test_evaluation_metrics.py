"""Unit tests for evaluation metrics calculation."""

import pytest

from zaikon.modules.evaluation.schemas import EvaluationCaseResult, MetricsReport
from zaikon.modules.evaluation.service import EvaluationService


class TestEvaluationMetrics:
    """Test metrics calculation for conflict detection evaluation."""

    def test_perfect_precision_and_recall(self):
        """Test metrics when all expected findings are detected and no false positives."""
        service = EvaluationService()
        
        results = [
            EvaluationCaseResult(
                case_id="test_001",
                title="Test case 1",
                passed=True,
                expected_finding_types=["deadline_mismatch", "competence_conflict"],
                actual_finding_types=["deadline_mismatch", "competence_conflict"],
                missing_finding_types=[],
            ),
            EvaluationCaseResult(
                case_id="test_002",
                title="Test case 2",
                passed=True,
                expected_finding_types=["authority_scope_conflict"],
                actual_finding_types=["authority_scope_conflict"],
                missing_finding_types=[],
            ),
        ]
        
        metrics = service._calculate_metrics(results)
        
        assert metrics.precision == 1.0, "Perfect detection should have 100% precision"
        assert metrics.recall == 1.0, "Perfect detection should have 100% recall"
        assert metrics.f1_score == 1.0, "Perfect detection should have F1 score of 1.0"
        assert metrics.true_positives == 3
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 0

    def test_false_positives_lower_precision(self):
        """Test that false positives lower precision but not recall."""
        service = EvaluationService()
        
        results = [
            EvaluationCaseResult(
                case_id="test_001",
                title="Test with false positive",
                passed=False,
                expected_finding_types=["deadline_mismatch"],
                actual_finding_types=["deadline_mismatch", "competence_conflict"],  # Extra finding
                missing_finding_types=[],
            ),
        ]
        
        metrics = service._calculate_metrics(results)
        
        assert metrics.precision == 0.5, "1 TP and 1 FP should give 50% precision"
        assert metrics.recall == 1.0, "All expected findings detected, recall should be 100%"
        assert metrics.true_positives == 1
        assert metrics.false_positives == 1
        assert metrics.false_negatives == 0

    def test_false_negatives_lower_recall(self):
        """Test that false negatives lower recall but not precision."""
        service = EvaluationService()
        
        results = [
            EvaluationCaseResult(
                case_id="test_001",
                title="Test with false negative",
                passed=False,
                expected_finding_types=["deadline_mismatch", "competence_conflict"],
                actual_finding_types=["deadline_mismatch"],  # Missing one
                missing_finding_types=["competence_conflict"],
            ),
        ]
        
        metrics = service._calculate_metrics(results)
        
        assert metrics.precision == 1.0, "No false positives, precision should be 100%"
        assert metrics.recall == 0.5, "1 of 2 expected findings detected, recall should be 50%"
        assert metrics.true_positives == 1
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 1

    def test_per_type_metrics(self):
        """Test that per-type metrics are calculated correctly."""
        service = EvaluationService()
        
        results = [
            EvaluationCaseResult(
                case_id="test_001",
                title="Test case 1",
                passed=True,
                expected_finding_types=["deadline_mismatch", "deadline_mismatch"],
                actual_finding_types=["deadline_mismatch", "deadline_mismatch"],
                missing_finding_types=[],
            ),
            EvaluationCaseResult(
                case_id="test_002",
                title="Test case 2",
                passed=False,
                expected_finding_types=["competence_conflict"],
                actual_finding_types=[],  # Missed
                missing_finding_types=["competence_conflict"],
            ),
        ]
        
        metrics = service._calculate_metrics(results)
        
        # Check per-type metrics
        assert "deadline_mismatch" in metrics.per_type_metrics
        assert "competence_conflict" in metrics.per_type_metrics
        
        deadline_metrics = metrics.per_type_metrics["deadline_mismatch"]
        assert deadline_metrics["precision"] == 1.0
        assert deadline_metrics["recall"] == 1.0
        assert deadline_metrics["expected_count"] == 2
        assert deadline_metrics["actual_count"] == 2
        
        competence_metrics = metrics.per_type_metrics["competence_conflict"]
        assert competence_metrics["precision"] == 0.0  # No detections
        assert competence_metrics["recall"] == 0.0  # Missed expected
        assert competence_metrics["expected_count"] == 1
        assert competence_metrics["actual_count"] == 0

    def test_f1_score_calculation(self):
        """Test F1 score calculation (harmonic mean of precision and recall)."""
        service = EvaluationService()
        
        results = [
            EvaluationCaseResult(
                case_id="test_001",
                title="Test case",
                passed=False,
                expected_finding_types=["type_a", "type_b", "type_c"],
                actual_finding_types=["type_a", "type_b"],  # Missing type_c
                missing_finding_types=["type_c"],
            ),
        ]
        
        metrics = service._calculate_metrics(results)
        
        # Precision = 2/2 = 1.0 (no false positives)
        # Recall = 2/3 = 0.667
        # F1 = 2 * (1.0 * 0.667) / (1.0 + 0.667) = 0.8
        assert metrics.precision == 1.0
        assert metrics.recall == round(2/3, 3)
        assert metrics.f1_score == 0.8

    def test_empty_results(self):
        """Test metrics calculation with no results."""
        service = EvaluationService()
        
        results = []
        
        metrics = service._calculate_metrics(results)
        
        assert metrics.precision == 0.0
        assert metrics.recall == 0.0
        assert metrics.f1_score == 0.0
        assert metrics.true_positives == 0
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 0

    def test_confusion_matrix(self):
        """Test confusion matrix generation."""
        service = EvaluationService()
        
        results = [
            EvaluationCaseResult(
                case_id="test_001",
                title="Test case",
                passed=False,
                expected_finding_types=["type_a", "type_b"],
                actual_finding_types=["type_a", "type_c"],  # type_b missed, type_c is FP
                missing_finding_types=["type_b"],
            ),
        ]
        
        metrics = service._calculate_metrics(results)
        
        # Check confusion matrix structure
        assert "true_positives_by_type" in metrics.confusion_matrix
        assert "false_positives_by_type" in metrics.confusion_matrix
        assert "false_negatives_by_type" in metrics.confusion_matrix
        
        # type_a: TP
        assert "type_a" in metrics.confusion_matrix["true_positives_by_type"]
        # type_c: FP
        assert "type_c" in metrics.confusion_matrix["false_positives_by_type"]
        # type_b: FN
        assert "type_b" in metrics.confusion_matrix["false_negatives_by_type"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
