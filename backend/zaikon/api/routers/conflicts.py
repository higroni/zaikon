"""Conflict taxonomy and registry endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from zaikon.modules.conflicts.schemas import (
    ConflictRuleRecord,
    ConflictTypeRecord,
    ConflictTypeRegistryResponse,
)
from zaikon.modules.conflicts.service import get_conflict_registry_service

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


@router.get("/types", response_model=ConflictTypeRegistryResponse)
def list_conflict_types(
    category: str | None = Query(default=None),
) -> ConflictTypeRegistryResponse:
    service = get_conflict_registry_service()
    conflict_types = service.list_conflict_types(category=category)
    return ConflictTypeRegistryResponse(
        conflict_types=conflict_types,
        total=len(conflict_types),
        categories=service.list_categories(),
    )


@router.post("/reload", response_model=ConflictTypeRegistryResponse)
def reload_conflict_registry() -> ConflictTypeRegistryResponse:
    service = get_conflict_registry_service()
    service.reload()
    conflict_types = service.list_conflict_types()
    return ConflictTypeRegistryResponse(
        conflict_types=conflict_types,
        total=len(conflict_types),
        categories=service.list_categories(),
    )


@router.get("/types/{finding_type}", response_model=ConflictTypeRecord)
def get_conflict_type(finding_type: str) -> ConflictTypeRecord:
    conflict_type = get_conflict_registry_service().get_conflict_type(finding_type)
    if conflict_type is None:
        raise HTTPException(status_code=404, detail="Conflict type not found")
    return conflict_type


class RuleUpdateRequest(BaseModel):
    """Request model for updating a conflict rule."""
    enabled: bool | None = None


@router.get("/rules", response_model=list[ConflictRuleRecord])
def list_conflict_rules() -> list[ConflictRuleRecord]:
    """List all conflict detection rules with their current status."""
    service = get_conflict_registry_service()
    # Convert ConflictTypeRecord to ConflictRuleRecord
    rules = []
    for ct in service.list_conflict_types():
        rules.append(
            ConflictRuleRecord(
                rule_id=ct.finding_type,
                conflict_type=ct.finding_type,
                category=ct.category,
                severity=ct.default_severity,
                description=ct.description,
                enabled=True,  # Default to enabled for now
                operators=[]  # Would come from active_rules.json
            )
        )
    return rules


@router.patch("/rules/{rule_id}", response_model=ConflictRuleRecord)
def update_conflict_rule(rule_id: str, update: RuleUpdateRequest) -> ConflictRuleRecord:
    """Update a conflict rule (e.g., enable/disable)."""
    service = get_conflict_registry_service()
    conflict_type = service.get_conflict_type(rule_id)
    
    if conflict_type is None:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    # Create rule record with updated status
    enabled = update.enabled if update.enabled is not None else True
    
    return ConflictRuleRecord(
        rule_id=conflict_type.finding_type,
        conflict_type=conflict_type.finding_type,
        category=conflict_type.category,
        severity=conflict_type.default_severity,
        description=conflict_type.description,
        enabled=enabled,
        operators=[]
    )
