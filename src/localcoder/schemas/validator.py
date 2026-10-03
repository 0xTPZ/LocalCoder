"""Validador mínimo do subconjunto de JSON Schema usado pelo LocalCoder."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .errors import SchemaValidationError


def _type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise SchemaValidationError(f"unsupported schema type: {expected}")


def _fail(path: str, message: str) -> None:
    raise SchemaValidationError(f"{path}: {message}")


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else expected
        if not any(_type_matches(instance, item) for item in expected_types):
            _fail(path, f"expected {expected_types}, got {type(instance).__name__}")

    if "enum" in schema and instance not in schema["enum"]:
        _fail(path, f"value is not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        minimum_length = schema.get("minLength")
        if minimum_length is not None and len(instance) < minimum_length:
            _fail(path, f"string length must be >= {minimum_length}")
        if schema.get("format") == "date-time":
            try:
                parsed = datetime.fromisoformat(instance.replace("Z", "+00:00"))
            except ValueError as exc:
                _fail(path, f"invalid date-time: {exc}")
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                _fail(path, "date-time must include an explicit UTC offset")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        minimum = schema.get("minimum")
        if minimum is not None and instance < minimum:
            _fail(path, f"number must be >= {minimum}")

    if isinstance(instance, dict):
        for required in schema.get("required", []):
            if required not in instance:
                _fail(path, f"missing required property {required!r}")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        if additional is False:
            unknown = sorted(set(instance) - set(properties))
            if unknown:
                _fail(path, f"unknown properties: {unknown!r}")
        for key, value in instance.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                validate(value, child_schema, f"{path}.{key}")
            elif isinstance(additional, dict):
                validate(value, additional, f"{path}.{key}")

    if isinstance(instance, list) and schema.get("items") is not None:
        for index, value in enumerate(instance):
            validate(value, schema["items"], f"{path}[{index}]")
