"""Corpus endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from typing import Any

from zaikon.modules.corpus.schemas import (
    CorpusRecord,
    CreateCorpusRequest,
    CreateCorpusResponse,
    ImportFolderRequest,
    ImportFolderResponse,
    ImportJobRecord,
    ImportReportResponse,
)
from zaikon.modules.corpus.service import get_corpus_service

router = APIRouter(prefix="/corpora", tags=["corpus"])
import_jobs_router = APIRouter(prefix="/import-jobs", tags=["corpus"])


@router.post("", response_model=CreateCorpusResponse)
def create_corpus(request: CreateCorpusRequest) -> CreateCorpusResponse:
    return get_corpus_service().create_corpus(request)


@router.get("", response_model=list[CorpusRecord])
def list_corpora() -> list[CorpusRecord]:
    return get_corpus_service().list_corpora()


@router.get("/{corpus_id}", response_model=CorpusRecord)
def get_corpus(corpus_id: UUID) -> CorpusRecord:
    corpus = get_corpus_service().get_corpus(corpus_id)
    if corpus is None:
        raise HTTPException(status_code=404, detail="Corpus not found")
    return corpus


@router.post("/{corpus_id}/import-folder", response_model=ImportFolderResponse)
def import_folder(corpus_id: UUID, request: ImportFolderRequest) -> ImportFolderResponse:
    if request.corpus_id != corpus_id:
        raise HTTPException(status_code=400, detail="corpus_id mismatch")
    try:
        return get_corpus_service().import_folder(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{corpus_id}/import-jobs", response_model=list[ImportJobRecord])
def list_import_jobs(corpus_id: UUID) -> list[ImportJobRecord]:
    return get_corpus_service().list_import_jobs(corpus_id)


@import_jobs_router.get("/{import_job_id}", response_model=ImportJobRecord)
def get_import_job(import_job_id: UUID) -> ImportJobRecord:
    job = get_corpus_service().get_import_job(import_job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


@import_jobs_router.get("/{import_job_id}/report", response_model=ImportReportResponse)
def get_import_report(import_job_id: UUID) -> ImportReportResponse:
    try:
        return get_corpus_service().get_import_report(import_job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@import_jobs_router.get("/{import_job_id}/artifacts", response_model=list[str])
def list_import_artifacts(import_job_id: UUID) -> list[str]:
    try:
        return get_corpus_service().list_import_artifacts(import_job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@import_jobs_router.get("/{import_job_id}/artifacts/{artifact_name}")
def get_import_artifact(import_job_id: UUID, artifact_name: str) -> dict[str, Any]:
    try:
        return get_corpus_service().get_import_artifact(import_job_id, artifact_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
