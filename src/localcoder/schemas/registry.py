"""Registry que controla versões e carrega schemas do repositório."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .errors import (
    SchemaNotFoundError,
    SchemaValidationError,
    UnknownSchemaVersionError,
    UnsupportedSchemaVersionError,
)
from .validator import validate


class SchemaRegistry:
    """Carrega schemas versionados e rejeita versões ambíguas."""

    CURRENT_VERSION = 1

    def __init__(self, root: Path | None = None) -> None:
        self.root = (root or Path(__file__).parents[3] / "schemas").resolve()
        self._cache: dict[tuple[str, int], dict[str, Any]] = {}

    def names(self) -> tuple[str, ...]:
        version_dir = self.root / f"v{self.CURRENT_VERSION}"
        if not version_dir.is_dir():
            return ()
        return tuple(sorted(path.stem for path in version_dir.glob("*.json")))

    def supported_versions(self, name: str) -> tuple[int, ...]:
        versions: list[int] = []
        for path in self.root.glob("v*" + "/" + f"{name}.json"):
            try:
                versions.append(int(path.parent.name[1:]))
            except ValueError:
                continue
        return tuple(sorted(versions))

    def load(self, name: str, version: int = CURRENT_VERSION) -> dict[str, Any]:
        key = (name, version)
        if key in self._cache:
            return self._cache[key]
        path = self.root / f"v{version}" / f"{name}.json"
        if not path.is_file():
            raise SchemaNotFoundError(f"schema not found: {name} v{version}")
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SchemaNotFoundError(f"schema cannot be read: {path}") from exc
        if not isinstance(schema, dict):
            raise SchemaNotFoundError(f"schema root is not an object: {path}")
        self._cache[key] = schema
        return schema

    def validate(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise SchemaValidationError("$: persisted document must be a JSON object")
        version = payload.get("schema_version")
        if isinstance(version, bool) or not isinstance(version, int):
            raise SchemaValidationError("$.schema_version: must be an integer")
        supported = self.supported_versions(name)
        if not supported:
            raise SchemaNotFoundError(f"schema not found: {name}")
        if version > max(supported):
            raise UnknownSchemaVersionError(f"unsupported future schema: {name} v{version}")
        if version not in supported:
            raise UnsupportedSchemaVersionError(f"unsupported schema: {name} v{version}")
        validate(payload, self.load(name, version))
        return payload

    def validate_many(self, documents: Iterable[tuple[str, dict[str, Any]]]) -> None:
        for name, payload in documents:
            self.validate(name, payload)
