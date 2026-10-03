"""Parsing e validação determinística de respostas estruturadas."""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..schemas.validator import validate
from .errors import StructuredOutputError


def parse_structured_output(text: str, schema: Mapping[str, Any]) -> Any:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError("structured response is not valid JSON") from exc
    try:
        validate(value, dict(schema))
    except ValueError as exc:
        raise StructuredOutputError("structured response does not satisfy the requested schema") from exc
    return value
