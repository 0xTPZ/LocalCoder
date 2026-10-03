"""Contratos de observação e coordenação de recursos."""

from .protocol import ResourceLease, ResourceManager, ResourceSnapshot

__all__ = ["ResourceLease", "ResourceManager", "ResourceSnapshot"]
