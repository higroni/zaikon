"""Gold-case evaluation runner for conflict detection."""

from functools import lru_cache
import json
from pathlib import Path
from uuid import uuid4

from zaikon.core.config import settings
from zaikon.modules.corpus.schemas import CreateCorpusRequest, ImportFolderRequest
from zaikon.modules.corpus.service import get_corpus_service
from zaikon.modules.draft_reviews.schemas import CreateDraftReviewRequest
from zaikon.modules.draft_reviews.service import get_draft_review_service
from zaikon.modules.evaluation.schemas import (
    EvaluationCase,
    EvaluationCaseResult,
    EvaluationRunResponse,
    MetricsReport,
)


class EvaluationService:
    """Runs deterministic gold cases through the existing import/review stack."""

    def __init__(self, rules_dir: Path | None = None) -> None:
        self.rules_dir = rules_dir or (
            settings.base_dir / "backend" / "zaikon" / "rules" / "evaluation"
        )

    def list_cases(self) -> list[EvaluationCase]:
        payload = json.loads((self.rules_dir / "gold_cases.json").read_text(encoding="utf-8"))
        return [EvaluationCase.model_validate(item) for item in payload.get("cases", [])]

    def run(self) -> EvaluationRunResponse:
        evaluation_run_id = uuid4()
        results = [
            self._run_case(evaluation_run_id=evaluation_run_id, case=case)
            for case in self.list_cases()
        ]
        passed_cases = sum(1 for result in results if result.passed)
        metrics = self._calculate_metrics(results)
        return EvaluationRunResponse(
            evaluation_run_id=evaluation_run_id,
            passed=passed_cases == len(results),
            total_cases=len(results),
            passed_cases=passed_cases,
            failed_cases=len(results) - passed_cases,
            results=results,
            metrics=metrics.model_dump(mode="json"),
        )

    def _run_case(
        self, *, evaluation_run_id, case: EvaluationCase
    ) -> EvaluationCaseResult:
        corpus_dir = self._write_case_corpus(evaluation_run_id, case)
        corpus = get_corpus_service().create_corpus(
            CreateCorpusRequest(name=f"Eval {case.case_id}")
        ).corpus
        get_corpus_service().import_folder(
            ImportFolderRequest(
                corpus_id=corpus.corpus_id,
                folder_uri=str(corpus_dir),
                recursive=False,
            )
        )
        draft_review = get_draft_review_service().create_draft_review(
            CreateDraftReviewRequest(
                title=case.draft.title,
                content_text=case.draft.text,
                selected_corpus_id=corpus.corpus_id,
            )
        ).draft_review
        run_response = get_draft_review_service().run_draft_review(
            draft_review.pipeline_run_id
        )
        actual_finding_types = [
            finding.finding_type for finding in run_response.findings
        ]
        expected_finding_types = [
            finding.finding_type for finding in case.expected_findings
        ]
        missing = [
            finding_type
            for finding_type in expected_finding_types
            if finding_type not in actual_finding_types
        ]
        return EvaluationCaseResult(
            case_id=case.case_id,
            title=case.title,
            passed=not missing,
            expected_finding_types=expected_finding_types,
            actual_finding_types=actual_finding_types,
            missing_finding_types=missing,
            pipeline_run_id=str(draft_review.pipeline_run_id),
            corpus_id=str(corpus.corpus_id),
            details={
                "finding_count": len(run_response.findings),
                "domain": case.domain,
            },
        )

    def _write_case_corpus(self, evaluation_run_id, case: EvaluationCase) -> Path:
        corpus_dir = (
            Path(settings.artifact_dir)
            / "evaluation"
            / str(evaluation_run_id)
            / case.case_id
            / "corpus"
        )
        corpus_dir.mkdir(parents=True, exist_ok=True)
        for document in case.corpus_documents:
            (corpus_dir / document.filename).write_text(
                document.text,
                encoding="utf-8",
            )
        return corpus_dir

    def _calculate_metrics(self, results: list[EvaluationCaseResult]) -> MetricsReport:
        """Calculate precision, recall, and F1 score from evaluation results."""
        # Aggregate all findings across all cases
        all_expected = []
        all_actual = []
        
        for result in results:
            all_expected.extend(result.expected_finding_types)
            all_actual.extend(result.actual_finding_types)
        
        # Calculate true positives, false positives, false negatives
        expected_set = set(all_expected)
        actual_set = set(all_actual)
        
        true_positives = len([ft for ft in all_actual if ft in all_expected])
        false_positives = len([ft for ft in all_actual if ft not in all_expected])
        false_negatives = len([ft for ft in all_expected if ft not in all_actual])
        
        # Calculate precision, recall, F1
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Per-type metrics
        per_type_metrics = {}
        unique_types = expected_set | actual_set
        
        for finding_type in unique_types:
            type_expected = all_expected.count(finding_type)
            type_actual = all_actual.count(finding_type)
            type_tp = min(type_expected, type_actual)
            type_fp = max(0, type_actual - type_expected)
            type_fn = max(0, type_expected - type_actual)
            
            type_precision = type_tp / (type_tp + type_fp) if (type_tp + type_fp) > 0 else 0.0
            type_recall = type_tp / (type_tp + type_fn) if (type_tp + type_fn) > 0 else 0.0
            type_f1 = 2 * (type_precision * type_recall) / (type_precision + type_recall) if (type_precision + type_recall) > 0 else 0.0
            
            per_type_metrics[finding_type] = {
                "precision": round(type_precision, 3),
                "recall": round(type_recall, 3),
                "f1_score": round(type_f1, 3),
                "expected_count": type_expected,
                "actual_count": type_actual,
                "true_positives": type_tp,
                "false_positives": type_fp,
                "false_negatives": type_fn,
            }
        
        # Confusion matrix
        confusion_matrix = {
            "true_positives_by_type": {ft: all_actual.count(ft) for ft in expected_set if ft in actual_set},
            "false_positives_by_type": {ft: all_actual.count(ft) for ft in actual_set if ft not in expected_set},
            "false_negatives_by_type": {ft: all_expected.count(ft) for ft in expected_set if ft not in actual_set},
        }
        
        return MetricsReport(
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1_score=round(f1_score, 3),
            true_positives=true_positives,
            false_positives=false_positives,
            false_negatives=false_negatives,
            total_expected=len(all_expected),
            total_actual=len(all_actual),
            per_type_metrics=per_type_metrics,
            confusion_matrix=confusion_matrix,
        )


@lru_cache
def get_evaluation_service() -> EvaluationService:
    return EvaluationService()
