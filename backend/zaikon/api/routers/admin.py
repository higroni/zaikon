"""Administrative data management endpoints."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from zaikon.core.config import settings

AdminDataType = Literal[
    "corpora",
    "import_jobs",
    "documents",
    "draft_reviews",
    "findings",
    "reports",
    "uploads",
    "vector_index",
]

DATA_TYPE_LABELS: dict[AdminDataType, str] = {
    "corpora": "korpusi i njihovi importovani dokumenti",
    "import_jobs": "import poslovi, reporti i import artefakti",
    "documents": "importovani dokumenti i SQLite mirror",
    "draft_reviews": "provere nacrta, artefakti i nalazi",
    "findings": "nalazi provere nacrta",
    "reports": "generisani izvestaji",
    "uploads": "upload folder",
    "vector_index": "lokalni vektorski indeks",
}

router = APIRouter(prefix="/admin/data", tags=["admin"])


class DataPurgeRequest(BaseModel):
    types: list[AdminDataType] = Field(min_length=1)


class DataMutationResponse(BaseModel):
    deleted: dict[str, int] = Field(default_factory=dict)
    restored: dict[str, int] = Field(default_factory=dict)
    message: str


@router.get("/types")
def list_data_types() -> dict[str, str]:
    return DATA_TYPE_LABELS


@router.post("/purge", response_model=DataMutationResponse)
def purge_data(request: DataPurgeRequest) -> DataMutationResponse:
    deleted: dict[str, int] = {}
    for data_type in request.types:
        deleted[data_type] = _purge_data_type(data_type)
    _reset_service_caches()
    return DataMutationResponse(
        deleted=deleted,
        message="Izabrani podaci su obrisani.",
    )


@router.get("/backup")
def backup_data() -> StreamingResponse:
    archive = io.BytesIO()
    manifest = {
        "format": "zaikon-data-dump",
        "version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "paths": {
            "artifact_dir": str(_artifact_dir()),
            "upload_dir": str(_upload_dir()),
            "database_path": str(_database_path()) if _database_path() else None,
            "qdrant_path": str(_qdrant_path()) if _qdrant_path() else None,
        },
    }
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as dump:
        dump.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        _zip_path(dump, _artifact_dir(), "artifacts")
        _zip_path(dump, _upload_dir(), "uploads")
        database_path = _database_path()
        if database_path and database_path.exists():
            dump.write(database_path, "database/zaikon.db")
        qdrant_path = _qdrant_path()
        if qdrant_path and qdrant_path.exists():
            _zip_path(dump, qdrant_path, "qdrant_storage")

    archive.seek(0)
    filename = f"zaikon-data-dump-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.zip"
    return StreamingResponse(
        archive,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore", response_model=DataMutationResponse)
async def restore_data(file: UploadFile = File(...)) -> DataMutationResponse:
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Dump fajl je prazan.")

    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as dump:
            if "manifest.json" not in dump.namelist():
                raise HTTPException(status_code=400, detail="Dump nema manifest.json.")
            manifest = json.loads(dump.read("manifest.json").decode("utf-8"))
            if manifest.get("format") != "zaikon-data-dump":
                raise HTTPException(status_code=400, detail="Dump nije zAIkon format.")
            restored = _restore_dump(dump)
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail="Dump nije validan ZIP fajl.") from exc

    _reset_service_caches()
    return DataMutationResponse(
        restored=restored,
        message="Dump je importovan i postojeći podaci su prepisani.",
    )


def _purge_data_type(data_type: AdminDataType) -> int:
    artifact_dir = _artifact_dir()
    if data_type == "corpora":
        count = _remove_path(artifact_dir / "corpus")
        count += _remove_database()
        return count
    if data_type == "import_jobs":
        count = _remove_path(artifact_dir / "corpus" / "import_jobs.json")
        count += _remove_path(artifact_dir / "corpus" / "import_reports")
        count += _remove_path(artifact_dir / "corpus" / "pipeline_artifacts")
        count += _remove_database()
        return count
    if data_type == "documents":
        count = _remove_path(artifact_dir / "corpus" / "pipeline_artifacts")
        count += _remove_database()
        return count
    if data_type == "draft_reviews":
        return _remove_path(artifact_dir / "draft_reviews")
    if data_type == "findings":
        return _remove_path(artifact_dir / "draft_reviews" / "findings")
    if data_type == "reports":
        return _remove_path(artifact_dir / "reports")
    if data_type == "uploads":
        return _remove_path(_upload_dir())
    if data_type == "vector_index":
        qdrant_path = _qdrant_path()
        return _remove_path(qdrant_path) if qdrant_path else 0
    raise ValueError(f"Unsupported data type: {data_type}")


def _restore_dump(dump: zipfile.ZipFile) -> dict[str, int]:
    restored: dict[str, int] = {}
    with tempfile.TemporaryDirectory(prefix="zaikon-restore-") as temp_name:
        temp_dir = Path(temp_name)
        _safe_extract(dump, temp_dir)

        restored["artifacts"] = _replace_path(temp_dir / "artifacts", _artifact_dir())
        restored["uploads"] = _replace_path(temp_dir / "uploads", _upload_dir())

        database_source = temp_dir / "database" / "zaikon.db"
        database_target = _database_path()
        if database_target:
            if database_source.exists():
                database_target.parent.mkdir(parents=True, exist_ok=True)
                if database_target.exists():
                    database_target.unlink()
                shutil.copy2(database_source, database_target)
                restored["database"] = 1
            else:
                restored["database"] = _remove_database()

        qdrant_target = _qdrant_path()
        if qdrant_target:
            restored["vector_index"] = _replace_path(
                temp_dir / "qdrant_storage",
                qdrant_target,
            )
    return restored


def _zip_path(dump: zipfile.ZipFile, source: Path, archive_prefix: str) -> None:
    source = source.resolve()
    if not source.exists():
        return
    if source.is_file():
        dump.write(source, archive_prefix)
        return
    for path in source.rglob("*"):
        if path.is_file():
            dump.write(path, f"{archive_prefix}/{path.relative_to(source).as_posix()}")


def _safe_extract(dump: zipfile.ZipFile, target: Path) -> None:
    target = target.resolve()
    for member in dump.infolist():
        destination = (target / member.filename).resolve()
        if destination != target and target not in destination.parents:
            raise HTTPException(status_code=400, detail="Dump sadrzi nebezbednu putanju.")
    dump.extractall(target)


def _replace_path(source: Path, target: Path) -> int:
    removed = _remove_path(target)
    if not source.exists():
        target.mkdir(parents=True, exist_ok=True)
        return removed
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
        return removed + _count_path(target)
    shutil.copy2(source, target)
    return removed + 1


def _remove_database() -> int:
    database_path = _database_path()
    if database_path is None:
        return 0
    return _remove_path(database_path)


def _remove_path(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    count = _count_path(path)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return count


def _count_path(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    return sum(1 for _ in path.rglob("*")) + 1


def _artifact_dir() -> Path:
    return settings.artifact_dir.resolve()


def _upload_dir() -> Path:
    return settings.upload_dir.resolve()


def _database_path() -> Path | None:
    if not settings.database_url.startswith("sqlite:///"):
        return None
    return Path(settings.database_url.removeprefix("sqlite:///")).resolve()


def _qdrant_path() -> Path | None:
    return settings.qdrant_path.resolve() if settings.qdrant_path else None


def _reset_service_caches() -> None:
    from zaikon.modules.assistant.service import get_assistant_service
    from zaikon.modules.corpus.service import get_corpus_service
    from zaikon.modules.reports.service import get_report_service

    get_assistant_service.cache_clear()
    get_corpus_service.cache_clear()
    get_report_service.cache_clear()
    # Note: get_draft_review_service does not use @lru_cache, so no cache_clear() needed
