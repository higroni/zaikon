"""Conflict registry and rule engine scaffolding."""

from zaikon.modules.conflicts.service import ConflictRegistryService
from zaikon.modules.conflicts.service import get_conflict_registry_service

__all__ = ["ConflictRegistryService", "get_conflict_registry_service"]
