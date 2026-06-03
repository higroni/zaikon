"""Ontology inspection endpoints."""

from fastapi import APIRouter

from zaikon.modules.ontology.schemas import OntologyResponse
from zaikon.modules.ontology.service import get_ontology_service

router = APIRouter(prefix="/ontology", tags=["ontology"])


@router.get("", response_model=OntologyResponse)
def get_ontology() -> OntologyResponse:
    return OntologyResponse(ontology=get_ontology_service().snapshot())


@router.post("/reload", response_model=OntologyResponse)
def reload_ontology() -> OntologyResponse:
    return OntologyResponse(ontology=get_ontology_service().reload())
