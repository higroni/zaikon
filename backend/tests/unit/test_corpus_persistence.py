"""Persistence tests for corpus artifact storage."""

from pathlib import Path

from zaikon.modules.corpus.schemas import CreateCorpusRequest, ImportFolderRequest
from zaikon.modules.corpus.service import CorpusService


FIXTURE_DIR = Path(__file__).parents[1] / "regression" / "fixtures" / "corpus_folder_import"


def test_corpus_service_persists_import_state_to_artifact_dir(tmp_path):
    service = CorpusService(artifact_dir=tmp_path)
    corpus = service.create_corpus(
        CreateCorpusRequest(name="Persistent corpus", language_code="sr")
    ).corpus

    import_response = service.import_folder(
        ImportFolderRequest(
            corpus_id=corpus.corpus_id,
            folder_uri=str(FIXTURE_DIR / "small_txt_corpus"),
        )
    )

    reloaded = CorpusService(artifact_dir=tmp_path)
    loaded_corpus = reloaded.get_corpus(corpus.corpus_id)
    loaded_job = reloaded.get_import_job(import_response.import_job.import_job_id)
    loaded_report = reloaded.get_import_report(
        import_response.import_job.import_job_id
    ).report

    assert loaded_corpus is not None
    assert loaded_corpus.name == "Persistent corpus"
    assert loaded_job is not None
    assert loaded_job.status == "completed"
    assert loaded_report.summary["stored_documents"] == 3
    assert "canonical_documents" in loaded_report.artifact_names
    assert (
        tmp_path
        / "corpus"
        / "pipeline_artifacts"
        / str(import_response.import_job.import_job_id)
        / "canonical_documents.json"
    ).exists()
