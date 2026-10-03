"""Primitivas para logs JSONL append-only com tolerância apenas no último registro."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..schemas import SchemaError, SchemaRegistry
from .locking import FileLock


class JsonlCorruptionError(RuntimeError):
    """Registro corrompido em posição que não é o último registro."""


@dataclass(frozen=True, slots=True)
class JsonlReadReport:
    documents: tuple[dict[str, Any], ...]
    ignored_final_record: bool = False
    issues: tuple[str, ...] = ()


def read_jsonl(path: Path, schema_name: str, registry: SchemaRegistry) -> JsonlReadReport:
    path = Path(path)
    if not path.is_file():
        return JsonlReadReport(())
    try:
        raw_lines = path.read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise JsonlCorruptionError(f"cannot read JSONL: {path}") from exc
    documents: list[dict[str, Any]] = []
    issues: list[str] = []
    ignored = False
    meaningful = [line for line in raw_lines if line.strip()]
    for index, raw_line in enumerate(meaningful):
        is_last = index == len(meaningful) - 1
        try:
            line = raw_line.decode("utf-8")
            document = json.loads(line)
            if not isinstance(document, dict):
                raise ValueError("record root is not an object")
            registry.validate(schema_name, document)
        except SchemaError as exc:
            raise JsonlCorruptionError(f"invalid schema in JSONL record at line {index + 1}: {path}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            if is_last:
                ignored = True
                issues.append(f"ignored final JSONL record at line {index + 1}: {type(exc).__name__}")
                break
            raise JsonlCorruptionError(f"corrupt JSONL record at line {index + 1}: {path}") from exc
        documents.append(document)
    return JsonlReadReport(tuple(documents), ignored, tuple(issues))


def append_jsonl_record(path: Path, document: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_BINARY, 0o600)
    with os.fdopen(descriptor, "ab") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def append_jsonl(path: Path, document: dict[str, Any], lock: FileLock) -> None:
    with lock:
        append_jsonl_record(path, document)
