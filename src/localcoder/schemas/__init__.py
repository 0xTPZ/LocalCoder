"""Schemas versionados e validação controlada de estado persistente."""

from .errors import (
    SchemaError,
    SchemaNotFoundError,
    SchemaValidationError,
    StateCorruptionError,
    UnknownSchemaVersionError,
    UnsupportedSchemaVersionError,
)
from .registry import SchemaRegistry

__all__ = [
    "SchemaError",
    "SchemaNotFoundError",
    "SchemaValidationError",
    "SchemaRegistry",
    "StateCorruptionError",
    "UnknownSchemaVersionError",
    "UnsupportedSchemaVersionError",
]
