"""Store JSON atômico, seguro contra estado inválido e compatível com Windows."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable

from ..schemas import (
    SchemaError,
    SchemaRegistry,
    StateCorruptionError,
    UnknownSchemaVersionError,
    UnsupportedSchemaVersionError,
)


class AtomicJsonStore:
    """Valida antes de substituir e escreve o temporário no mesmo volume."""

    def __init__(self, path: Path, schema_name: str, registry: SchemaRegistry | None = None) -> None:
        self.path = Path(path)
        self.schema_name = schema_name
        self.registry = registry or SchemaRegistry()

    def save(
        self,
        payload: dict[str, Any],
        *,
        before_replace: Callable[[Path], None] | None = None,
    ) -> None:
        """Valida, grava, flush/fsync e troca atomicamente.

        `before_replace` existe apenas para testes de interrupção simulada; produção não deve
        depender dele.
        """

        self.registry.validate(self.schema_name, payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
            )
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            if before_replace is not None:
                before_replace(temporary)
            # Same-directory os.replace is atomic on the supported Windows/filesystem path.
            os.replace(temporary, self.path)
            temporary = None
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass

    def load(self) -> dict[str, Any]:
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StateCorruptionError(f"cannot decode persisted state: {self.path}") from exc
        try:
            self.registry.validate(self.schema_name, payload)
        except (UnknownSchemaVersionError, UnsupportedSchemaVersionError):
            raise
        except SchemaError as exc:
            raise StateCorruptionError(f"persisted state failed validation: {self.path}: {exc}") from exc
        return payload
