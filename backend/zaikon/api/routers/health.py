"""Health endpoints."""

from fastapi import APIRouter

from zaikon.core.schemas import ModuleHealth

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ModuleHealth)
def health() -> ModuleHealth:
    return ModuleHealth(module_name="zaikon-api")


@router.get("/api/v1/modules/health", response_model=list[ModuleHealth])
def modules_health() -> list[ModuleHealth]:
    return [
        ModuleHealth(module_name="corpus"),
        ModuleHealth(module_name="documents"),
        ModuleHealth(module_name="legal_parser"),
        ModuleHealth(module_name="canonical"),
        ModuleHealth(module_name="references"),
        ModuleHealth(module_name="indexing"),
        ModuleHealth(module_name="retrieval"),
        ModuleHealth(module_name="checkers"),
        ModuleHealth(module_name="llm"),
        ModuleHealth(module_name="reports"),
    ]

