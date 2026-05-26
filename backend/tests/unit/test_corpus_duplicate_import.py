"""Duplicate handling tests for corpus import."""

from zaikon.pipeline.steps.corpus.folder_import import CorpusFolderImportChain


def test_corpus_folder_import_skips_duplicate_supported_files(tmp_path):
    content = """Zakon o duplikatima

Clan 1.
Isti tekst.
"""
    (tmp_path / "a.txt").write_text(content, encoding="utf-8")
    (tmp_path / "b.txt").write_text(content, encoding="utf-8")

    context = CorpusFolderImportChain().run({"folder_uri": str(tmp_path)})

    report = context.get_artifact("import_report").payload
    assert report["summary"]["total_files"] == 2
    assert report["summary"]["supported_files"] == 1
    assert report["summary"]["duplicate_files"] == 1
    assert report["summary"]["extracted_documents"] == 1
    assert [warning["code"] for warning in report["warnings"]] == ["duplicate_file"]
    assert len(context.get_artifact("canonical_documents").payload) == 1
